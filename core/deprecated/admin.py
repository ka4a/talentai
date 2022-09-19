from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sites.shortcuts import get_current_site
from django.db import DatabaseError, transaction
from django.template.loader import render_to_string
from modeltranslation.admin import TranslationAdmin

from core import models as m
from core.admin import ExtendedVersionAdmin, LogAdminMixin, OrgAdmin, ExtendedModelAdmin
from core.tasks import send_email


admin.site.register(m.Contract, ExtendedVersionAdmin)
admin.site.register(m.Fee, ExtendedVersionAdmin)


@admin.register(m.AgencyCategory)
class AgencyCategoryAdmin(LogAdminMixin, TranslationAdmin):
    list_display = ('group', 'title_en', 'title_ja')
    list_filter = ('group',)
    search_fields = ('title_en', 'title_ja')


@admin.register(m.Agency)
class AgencyAdmin(OrgAdmin):
    list_display = ('name', 'email_domain', 'contact_email', 'has_members')

    def has_members(self, obj):
        return obj.members.exists()

    def get_form(self, request, obj=None, **kwargs):
        """Restrict primary contract choices to agency members"""
        form = super().get_form(request, obj, **kwargs)
        if obj is not None:
            form.base_fields['primary_contact'].queryset = obj.members
        return form

    has_members.boolean = True


@admin.register(m.AgencyInvite)
class AgencyInviteAdmin(ExtendedModelAdmin):
    list_display = ('email', 'private_note', 'created_at', 'used_by', 'url')

    def url(self, obj):
        return '{}{}'.format(settings.BASE_URL, obj.get_absolute_url())

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not change:
            current_site = get_current_site(request)
            context = {
                'site_name': current_site.name,
                'base_url': settings.BASE_URL,
                'token': obj.token,
            }
            subject = render_to_string('agency_invite/subject.txt', context)
            subject = ''.join(subject.splitlines())

            send_email.delay(
                subject=subject,
                body=render_to_string('agency_invite/body.txt', context),
                to=[obj.email],
            )


@admin.register(m.AgencyRegistrationRequest)
class AgencyRegistrationRequestAdmin(ExtendedVersionAdmin):
    readonly_fields = ('ip', 'headers')
    list_display = ('id', 'name', 'get_user_info', 'created')

    actions = ['create_agency']

    ERROR_USER_EMAIL_EXISTS = (
        'An error occurred while creating user for {}. '
        'The email address is already used'
    )

    def get_user_info(self, obj):
        return '{} {} ({})'.format(
            obj.user.first_name, obj.user.last_name, obj.user.email
        )

    get_user_info.short_description = 'Contact'

    def create_agency(self, request, queryset):
        created_objects = []
        errors = []

        for r in queryset.filter(created=False):
            try:
                created_objects.append(r.approve())
            except DatabaseError:
                errors.append('An error occurred while creating {}'.format(r.name))

        self.message_user(
            request,
            render_to_string(
                'admin_messages/agencies_created.html',
                {'created_objects': created_objects, 'errors': errors},
            ),
        )

    create_agency.short_description = 'Create selected agencies'


@admin.register(m.ClientRegistrationRequest)
class ClientRegistrationRequestAdmin(ExtendedVersionAdmin):
    readonly_fields = ('ip', 'headers')
    list_display = ('id', 'name', 'get_user_info', 'created')

    actions = ['create_client']

    ERROR_USER_EMAIL_EXISTS = (
        'An error occurred while creating user for "{}". '
        'The email address is already used'
    )

    def get_user_info(self, obj):
        return '{} {} ({})'.format(
            obj.user.first_name, obj.user.last_name, obj.user.email
        )

    get_user_info.short_description = 'Contact'

    def create_client(self, request, queryset):
        created_objects = []
        errors = []

        for r in queryset.filter(created=False):
            try:
                with transaction.atomic():
                    r.user.groups.add(Group.objects.get(name='Client Administrators'))

                    client = m.Client.objects.create(
                        name=r.name, primary_contact=r.user, country=r.country,
                    )

                    m.ClientAdministrator.objects.create(user=r.user, client=client)

                    r.created = True
                    r.save()

                    created_objects.append(client)
            except DatabaseError:
                errors.append('An error occurred while creating "{}"'.format(r.name))

        self.message_user(
            request,
            render_to_string(
                'admin_messages/clients_created.html',
                {'created_objects': created_objects, 'errors': errors},
            ),
        )

    create_client.short_description = 'Create selected clients'
