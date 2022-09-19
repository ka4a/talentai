import functools
import logging

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.widgets import AutocompleteSelect
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.db import DatabaseError, transaction
from django.db.models.query_utils import Q
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from import_export import resources
from import_export.admin import ImportMixin
from modeltranslation.admin import TranslationAdmin
from ordered_model.admin import OrderedTabularInline, OrderedInlineModelAdminMixin
from reversion.admin import VersionAdmin

from core import models as m
from core.zoho import validate_zoho_auth_token
from core.forms import (
    ClientRoleInlineFormSet,
    UserForm,
    CandidateImportForm,
    CandidateConfirmImportForm,
)
from .tasks import send_email
from .user_activation import activate_user


class OrganizationClientListFilter(admin.SimpleListFilter):
    """
    Client filter for most cases. Checks for `organization` generic foreign key.
    Does nothing for models without that foreign key.
    """

    title = _('client')
    parameter_name = 'client'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuple(org_id, client_name)
        """
        organization = getattr(model_admin.model, 'organization', None)
        if type(organization) != GenericForeignKey:
            return []

        ct_field = organization.ct_field
        self.fk_field = organization.fk_field
        queryset = model_admin.get_queryset(request).filter(
            **{
                ct_field: ContentType.objects.get_for_model(
                    m.Client, for_concrete_model=False
                )
            }
        )
        return (
            queryset.values_list(self.fk_field, 'client__name')
            .order_by(self.fk_field)
            .distinct(self.fk_field)
        )

    def queryset(self, request, queryset):
        return queryset.filter(**{self.fk_field: self.value()})


class ExtendedChangeList(ChangeList):
    """
    Extended to return none if filters aren't selected.
    Used by `LogAdminMixin`.
    """

    def get_queryset(self, request):
        (
            self.filter_specs,
            self.has_filters,
            _,
            _,
            self.has_active_filters,
        ) = self.get_filters(request)
        if not self.has_active_filters and self.has_filters:
            return self.root_queryset.none()
        return super().get_queryset(request)


class CandidateResource(resources.ModelResource):
    """
    Used for importing Candidates
    """

    class Meta:
        model = m.Candidate
        fields = (
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'first_name_kanji',
            'last_name_kanji',
            'first_name_katakana',
            'last_name_katakana',
            'birthdate',
            'nationality',
            'gender',
            'email',
            'secondary_email',
            'phone',
            'secondary_phone',
            'current_street',
            'current_city',
            'current_prefecture',
            'current_postal_code',
            'current_country',
            'linkedin_url',
            'github_url',
            'website_url',
            'twitter_url',
            'current_position',
            'current_company',
            'current_salary',
            'current_salary_variable',
            'current_salary_breakdown',
            'employment_status',
            'tax_equalization',
            'max_num_people_managed',
        )

    def after_import_instance(self, instance, new, row_number=None, **kwargs):
        instance.org_id = kwargs['org_id']
        instance.org_content_type = kwargs['org_content_type']

    @classmethod
    def field_from_django_field(cls, field_name, django_field, readonly):
        """
        Returns a Resource Field instance for the given Django model field.
        Note: overridden because the original doesn't check for `saves_null_values`
        """
        FieldWidget = cls.widget_from_django_field(django_field)
        widget_kwargs = cls.widget_kwargs_for_field(field_name)
        field = cls.DEFAULT_RESOURCE_FIELD(
            attribute=field_name,
            column_name=field_name,
            widget=FieldWidget(**widget_kwargs),
            readonly=readonly,
            default=django_field.default,
            saves_null_values=django_field.null,
        )
        return field


class ZohoAdminMixin(object):
    def validate_zoho_auth_token(self, request, obj):
        try:
            zoho_token_is_invalid = (
                obj.zoho_auth_token
                and not validate_zoho_auth_token(obj.zoho_auth_token)
            )

            if zoho_token_is_invalid:
                self.message_user(
                    request, 'Invalid Zoho Auth Token.', level=messages.ERROR
                )
        except Exception as e:
            logging.exception(e)
            self.message_user(
                request, 'Could not validate Zoho Auth Token.', level=messages.ERROR
            )


class LogAdminMixin:
    """
    Mixin for creating logs for views
    """

    def get_changelist(self, request, **kwargs):
        return ExtendedChangeList

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        if response.status_code == 200 and request.method == 'GET':
            m.LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=m.ContentType.objects.get_for_model(
                    self.model, for_concrete_model=False
                ).pk,
                object_id=None,
                object_repr=f"List of {self.model}",
                action_flag=m.LogEntry.ActionFlag.VIEW,
                change_message=request.get_full_path(),
            )
        return response

    def change_view(self, request, object_id, form_url='', extra_context=None):
        response = super().change_view(request, object_id, form_url, extra_context)
        if response.status_code == 200 and request.method == 'GET':
            m.LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=m.ContentType.objects.get_for_model(
                    self.model, for_concrete_model=False
                ).pk,
                object_id=object_id,
                object_repr=str(self.model.objects.get(pk=object_id)),
                action_flag=m.LogEntry.ActionFlag.VIEW,
                change_message=request.get_full_path(),
            )
        return response


class StaffAccessMixin:
    """
    Mixin for staff-based permissions. To use, add a `staff_access` attribute:
    
    staff_access = ['view', 'add', 'change', 'delete']
    """

    staff_access = []

    def has_view_permission(self, request, obj=None):
        if request.user.is_staff and 'view' in self.staff_access:
            return True
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        if request.user.is_staff and 'add' in self.staff_access:
            return True
        if obj is None:
            return super().has_add_permission(request)
        else:
            # inline model
            return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff and 'change' in self.staff_access:
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_staff and 'delete' in self.staff_access:
            return True
        return super().has_delete_permission(request, obj)

    def has_module_permission(self, request):
        if request.user.is_staff and self.staff_access:
            return True
        return super().has_module_permission(request)


class ExtendedModelAdmin(StaffAccessMixin, LogAdminMixin, admin.ModelAdmin):
    list_filter = (OrganizationClientListFilter,)


class ExtendedVersionAdmin(StaffAccessMixin, LogAdminMixin, VersionAdmin):
    list_filter = (OrganizationClientListFilter,)


class TeamInline(GenericTabularInline):
    model = m.Team
    extra = 0
    ct_field = 'org_content_type'
    ct_fk_field = 'org_id'


class OrgAdmin(ZohoAdminMixin, ExtendedVersionAdmin):
    inlines = (TeamInline,)

    def save_model(self, request, obj, form, change):
        self.validate_zoho_auth_token(request, obj)
        super().save_model(request, obj, form, change)


admin.site.register(m.CandidateNote, ExtendedVersionAdmin)


@admin.register(m.ProposalInterviewSchedule)
class ProposalInterviewScheduleAdmin(ExtendedModelAdmin):
    list_filter = ('interview__proposal__job__owner_client',)


@admin.register(m.ProposalInterviewScheduleTimeSlot)
class ProposalInterviewScheduleTimeSlotAdmin(ExtendedModelAdmin):
    list_filter = ('schedule__interview__proposal__job__owner_client',)


@admin.register(m.ProposalInterview)
class ProposalInterviewAdmin(ExtendedVersionAdmin):
    list_filter = ('proposal__job__owner_client',)


@admin.register(m.Tag)
class TagAdmin(ExtendedVersionAdmin):
    list_display = ('name', 'organization', 'type')
    staff_access = ['view']


@admin.register(m.Candidate)
class CandidateAdmin(ImportMixin, ExtendedVersionAdmin):
    list_display = ('name', 'archived')
    list_filter = ('client',)
    ordering = ('archived',)
    readonly_fields = ('original',)
    resource_class = CandidateResource

    actions = ['archive_selected', 'recover_selected']

    def get_queryset(self, request):
        return m.Candidate.archived_objects.all()

    def archive_selected(self, request, queryset):
        """Archive candidates instead of deleting them"""
        queryset.update(archived=True)

    def recover_selected(self, request, queryset):
        queryset.update(archived=False)

    archive_selected.short_description = 'Archive selected candidates'
    recover_selected.short_description = 'Recover selected candidates'

    def get_import_form(self):
        return CandidateImportForm

    def get_confirm_import_form(self):
        return CandidateConfirmImportForm

    def get_import_data_kwargs(self, request, form, *args, **kwargs):
        kwargs = super().get_import_data_kwargs(request, form, *args, **kwargs)
        organization = form.cleaned_data['organization']
        kwargs.update(
            {
                'org_id': organization.id,
                'org_content_type': m.ContentType.objects.get_for_model(organization),
            }
        )
        return kwargs

    def get_form_kwargs(self, form, *args, **kwargs):
        # pass on `organization` to the kwargs for the custom confirm form
        if isinstance(form, CandidateImportForm):
            if form.is_valid():
                organization = form.cleaned_data['organization']
                kwargs.update({'organization': organization.id})
        return kwargs


@admin.register(m.ProposalStatus)
class ProposalStatusAdmin(StaffAccessMixin, TranslationAdmin):
    list_display = (
        'group',
        'status_en',
        'status_ja',
        'deal_stage',
        'default',
        'default_order',
    )
    list_filter = ('group', 'default')
    search_fields = ('status',)
    ordering = ('status',)
    staff_access = ['view']


@admin.register(m.OrganizationProposalStatus)
class OrganizationProposalStatusAdmin(ExtendedModelAdmin):
    list_display = ('organization', 'status', 'order')
    ordering = ('org_id', 'org_content_type', 'order')


class ClientRoleInline(admin.TabularInline):
    fields = (
        'user',
        'name',
    )
    readonly_fields = ('name',)
    show_change_link = True
    formset = ClientRoleInlineFormSet
    extra = 0

    def filter_users(self, queryset):
        return queryset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            db = kwargs.get('using')
            if request.method == 'GET':  # to allow newly created users to be added
                try:
                    client = m.Client.objects.get(
                        pk=request.resolver_match.kwargs.get('object_id')
                    )
                    kwargs['queryset'] = client.members
                except Exception:
                    # new client so no need for this
                    pass
            kwargs['widget'] = AutocompleteSelect(
                db_field.remote_field,
                self.admin_site,
                attrs={'readonly': 'readonly'},
                using=db,
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ClientAdministratorInline(StaffAccessMixin, ClientRoleInline):
    model = m.ClientAdministrator
    staff_access = ['add', 'change', 'view']


class ClientInternalRecruiterInline(StaffAccessMixin, ClientRoleInline):
    model = m.ClientInternalRecruiter
    staff_access = ['add', 'change', 'view']


class ClientStandardUserInline(StaffAccessMixin, ClientRoleInline):
    model = m.ClientStandardUser
    staff_access = ['add', 'change', 'view']


@admin.register(m.Client)
class ClientAdmin(OrgAdmin):
    inlines = (
        TeamInline,
        ClientAdministratorInline,
        ClientInternalRecruiterInline,
        ClientStandardUserInline,
    )
    change_form_template = 'admin/client/change_form.html'
    staff_access = ['add', 'change', 'view']

    def get_form(self, request, obj=None, **kwargs):
        """Restrict primary contract choices to client members"""
        form = super().get_form(request, obj, **kwargs)
        if obj is not None:
            form.base_fields['primary_contact'].queryset = obj.members
        else:
            form.base_fields['primary_contact'].queryset = m.User.objects.filter(
                Q(clientadministrator=None)
                & Q(clientinternalrecruiter=None)
                & Q(clientstandarduser=None)
                & Q(agencyadministrator=None)
                & Q(agencymanager=None)
                & Q(recruiter=None)
            )
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not hasattr(obj.primary_contact, 'clientadministrator'):
            obj.primary_contact.groups.clear()
            m.ClientAdministrator.objects.get_or_create(
                user=obj.primary_contact, client=obj
            )
            obj.primary_contact.groups.add(
                Group.objects.get(name='Client Administrators')
            )

    def save_formset(self, request, form, formset, change):
        if formset.model not in {
            m.ClientAdministrator,
            m.ClientInternalRecruiter,
            m.ClientStandardUser,
        }:
            return super().save_formset(request, form, formset, change)

        group = Group.objects.get(name=formset.model.group_name)
        instances = formset.save()
        for instance in instances:
            instance.user.groups.clear()
            instance.user.groups.add(group)


@admin.register(m.Function)
class FunctionAdmin(ExtendedModelAdmin):
    list_display = ('title_en', 'title_ja')
    staff_access = ['view']


@admin.register(m.Feedback)
class FeedbackAdmin(ExtendedModelAdmin):
    list_display = ('text', 'page_url', 'created_by', 'created_at')
    staff_access = ['view']


@admin.register(m.Team)
class TeamAdmin(ExtendedModelAdmin):
    # TODO: add a way to filter by client/agency?
    list_display = ('name', 'organization')


class JobQuestionInline(admin.TabularInline):
    model = m.JobQuestion
    extra = 0


class JobInterviewTemplateInline(admin.TabularInline):
    model = m.JobInterviewTemplate
    extra = 0


@admin.register(m.ProposalComment)
class ProposalCommentAdmin(ExtendedVersionAdmin):
    list_display = ('id', 'proposal', 'author', 'created_at')
    list_filter = ('proposal__job__owner_client',)


@admin.register(m.Job)
class JobAdmin(ExtendedVersionAdmin):
    inlines = [JobQuestionInline, JobInterviewTemplateInline]

    def get_form(self, request, obj=None, **kwargs):
        """Restrict Manager choices to Client's Hiring Managers."""
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['_managers'].queryset = obj.client.members.all()
        return form


class HiringManagerInline(admin.StackedInline):
    model = m.HiringManager


class TalentAssociateInline(admin.StackedInline):
    model = m.TalentAssociate


class AgencyProfileInline(admin.StackedInline):
    """Inline for Agency Users with teams field."""

    def get_formset(self, request, obj=None, **kwargs):
        """Show only Teams belonging to the Agency of the Recuriter."""
        formset = super().get_formset(request, obj, **kwargs)

        if not obj:
            return formset

        if hasattr(obj.profile, 'agency'):
            teams = formset.form.base_fields['teams'].queryset.filter(
                agency=obj.profile.agency
            )
            formset.form.base_fields['teams'].queryset = teams
        elif hasattr(obj.profile, 'client'):
            teams = formset.form.base_fields['teams'].queryset.filter(
                client=obj.profile.client
            )
            formset.form.base_fields['teams'].queryset = teams

        return formset


class AgencyAdministratorInline(AgencyProfileInline):
    model = m.AgencyAdministrator


class AgencyManagerInline(AgencyProfileInline):
    model = m.AgencyManager


class RecruiterInline(AgencyProfileInline):
    model = m.Recruiter


@admin.register(m.User)
class UserAdminExtended(ExtendedVersionAdmin, UserAdmin):
    form = UserForm
    change_form_template = 'admin/user_extended/change_form.html'
    add_form_template = 'admin/user_extended/add_form.html'
    superuser_fieldsets = (
        (None, {'fields': ('email', 'password', 'zoho_id')}),
        (_('Profile'), {'fields': ('role', 'client', 'agency')}),
        (
            _('Personal info'),
            {'fields': ('first_name', 'last_name', 'locale', 'country', 'zoho_data')},
        ),
        (
            _('Permissions'),
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')},
        ),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    staff_fieldsets = (
        (None, {'fields': ('email', 'password', 'zoho_id')}),
        (_('Profile'), {'fields': ('role', 'client', 'agency')}),
        (
            _('Personal info'),
            {'fields': ('first_name', 'last_name', 'locale', 'country', 'zoho_data')},
        ),
        (_('Permissions'), {'fields': ('is_active', 'is_staff')},),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'first_name',
                    'last_name',
                    'password1',
                    'password2',
                    'is_staff',
                ),
            },
        ),
    )

    list_display = (
        'email',
        'first_name',
        'last_name',
        'profile',
        'is_staff',
        'is_activated',
    )
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email',)
    actions = ['activate_user']
    staff_access = ['add', 'change', 'view']

    def get_queryset(self, request):
        if request.user.is_staff and not request.user.is_superuser:
            return m.User.objects.filter(is_superuser=False)
        return super().get_queryset(request)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        if request.user.is_staff and not request.user.is_superuser:
            return self.staff_fieldsets
        return self.superuser_fieldsets

    def get_form(self, request, obj=None, **kwargs):
        is_popup = request.GET.get('_popup') == '1'
        Form = super().get_form(request, obj, **kwargs)
        if is_popup and obj is not None:
            return functools.partial(Form, is_popup=is_popup)
        else:
            return Form

    def activate_user(self, request, queryset):
        """Run the User activation process."""
        activated_users = []
        errors = []

        for u in queryset.filter(is_activated=False):
            try:
                activate_user(u)
                activated_users.append(u)
            except DatabaseError:
                errors.append('An error occurred while creating {}'.format(u.email))

        self.message_user(
            request,
            render_to_string(
                'admin_messages/users_activated.html',
                {'activated_users': activated_users, 'errors': errors},
            ),
        )

    activate_user.short_description = 'Activate selected users'


@admin.register(m.SkillDomain)
class SkillDomainAdmin(ExtendedVersionAdmin):
    list_display = ('name',)


@admin.register(m.InterviewTemplate)
class InterviewTemplateAdmin(ExtendedModelAdmin):
    list_display = ('interview_type', 'default_order')
    staff_access = ['view']


@admin.register(m.LegalAgreement)
class LegalAgreementAdmin(ExtendedModelAdmin):
    list_display = ('document_type', 'version', 'is_draft')
    staff_access = ['add', 'change', 'view']


@admin.register(m.ReasonNotInterestedCandidateOption)
class ReasonNotInterestedCandidateOptionAdmin(ExtendedVersionAdmin):
    staff_access = ['view']


@admin.register(m.ReasonDeclineCandidateOption)
class ReasonDeclineCandidateOption(ExtendedVersionAdmin):
    staff_access = ['view']


class ProposalInterviewTabularInline(OrderedTabularInline):
    model = m.ProposalInterview
    fields = (
        'current_schedule',
        'interview_type',
        'interviewer',
        'description',
        'order',
        'move_up_down_links',
    )
    readonly_fields = (
        'order',
        'move_up_down_links',
    )
    extra = 1
    ordering = ('order',)


@admin.register(m.Proposal)
class ProposalAdmin(OrderedInlineModelAdminMixin, ExtendedVersionAdmin):
    inlines = (ProposalInterviewTabularInline,)
    list_filter = ('job__owner_client',)
    fields = (
        'job',
        'candidate',
        'status',
        'status_last_updated_by',
        'is_direct_application',
        'is_rejected',
    )
    readonly_fields = (
        'job',
        'candidate',
    )


@admin.register(m.LogEntry)
class LogEntryAdmin(StaffAccessMixin, admin.ModelAdmin):
    date_hierarchy = 'action_time'
    staff_access = ['view']

    fields = [
        'action_time',
        'user',
        'content_type',
        'object_id',
        'object_repr',
        'action_flag_display',
        'message_display',
    ]

    list_filter = [
        'user',
        'content_type',
        'action_flag',
    ]

    search_fields = ['object_repr', 'change_message']

    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag_display',
    ]

    def get_queryset(self, request):
        return m.LogEntry.objects.all()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        return mark_safe(escape(obj.object_repr))

    object_link.admin_order_field = "object_repr"
    object_link.short_description = "object"

    def action_flag_display(self, obj):
        return obj.get_action_flag_display()

    action_flag_display.short_description = 'action flag'

    def message_display(self, obj):
        return obj.change_message

    message_display.short_description = 'message'
