from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.db.transaction import atomic
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _

from import_export.forms import ImportForm, ConfirmImportForm

from core.models import (
    Client,
    Agency,
    ClientAdministrator,
    ClientInternalRecruiter,
    ClientStandardUser,
    AgencyAdministrator,
    AgencyManager,
    Recruiter,
    User,
)


class RoleChoices:
    def __init__(self, choices):
        i = 0

        self.map = dict()
        self.choices = list()
        for model, name in choices:
            key = str(i)
            for attr in ('client', 'agency'):
                if hasattr(model, attr):
                    key = f'{key},{attr}'
            self.choices.append((key, name))
            self.map[key] = model
            i += 1

    def get(self, key, default=None):
        return self.map.get(key, default)

    def get_key(self, value):
        for key in self.map:
            if type(value) == self.map[key]:
                return key


roles = RoleChoices(
    (
        (None, '---------'),
        (ClientAdministrator, 'Client Administrator'),
        (ClientInternalRecruiter, 'Client Internal Recruiter'),
        (ClientStandardUser, 'Client Standard User'),
        (AgencyAdministrator, 'Agency Administrator'),
        (AgencyManager, 'Agency Manager'),
        (Recruiter, 'Recruiter'),
    )
)
client_roles = RoleChoices(
    (
        (ClientAdministrator, 'Client Administrator'),
        (ClientInternalRecruiter, 'Client Internal Recruiter'),
        (ClientStandardUser, 'Client Standard User'),
    )
)
agency_roles = RoleChoices(
    (
        (AgencyAdministrator, 'Agency Administrator'),
        (AgencyManager, 'Agency Manager'),
        (Recruiter, 'Recruiter'),
    )
)


class UserForm(forms.ModelForm):
    role = forms.ChoiceField(choices=roles.choices)
    agency = forms.ModelChoiceField(
        queryset=Agency.objects.all(), required=False, empty_label=None,
    )
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(), required=False, empty_label=None,
    )
    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_(
            "Raw passwords are not stored, so there is no way to see this "
            "user's password, but you can change the password using "
            "<a href=\"{}\">this form</a>."
        ),
    )

    def __init__(self, *args, **kwargs):
        self.is_popup = kwargs.pop('is_popup', False)
        super().__init__(*args, **kwargs)
        password = self.fields.get('password')
        if password:
            password.help_text = password.help_text.format('../password/')
        self.roles = roles
        if self.is_popup:
            if hasattr(self.instance.profile, 'client'):
                self.roles = client_roles
            elif hasattr(self.instance.profile, 'agency'):
                self.roles = agency_roles
        self.fields['role'].choices = self.roles.choices

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial.get('password')

    def get_role(self):
        role_id = self.cleaned_data.get('role', None)
        return self.roles.get(role_id)

    @atomic
    def update_profile(self, instance):
        role = self.get_role()

        is_new_role = True

        for attr, old_profile in instance.get_profile_attribute_pair_iterator():
            if role and type(old_profile) == role:
                is_new_role = False
                self.set_profile_org(old_profile)
                old_profile.save()
            else:
                instance.delete_profile(attr)

        if not role or is_new_role:
            instance.groups.clear()

        if role and is_new_role:
            profile = role()

            instance.assign_profile_group(role)

            profile.user = instance
            self.set_profile_org(profile)

            profile.save()

    def clean(self):
        result = super().clean()
        role = self.get_role()
        for field in ('client', 'agency'):
            if hasattr(role, field):
                org = self.cleaned_data.get(field, None)
                if not org:
                    raise ValidationError(
                        {field: getattr(self, field).error_messages['required']}
                    )
        return result

    def get_initial_for_field(self, field, field_name):
        if self.instance:
            if field_name == 'role':
                return self.roles.get_key(self.instance.first_profile)

            if field_name == 'client':
                return getattr(self.instance.first_profile, 'client', None)

            if field_name == 'agency':
                return getattr(self.instance.first_profile, 'agency', None)

        return super().get_initial_for_field(field, field_name)

    def set_profile_org(self, profile):
        for attr in ('client', 'agency'):
            if hasattr(type(profile), attr):
                org = self.cleaned_data.get(attr, None)
                setattr(profile, attr, org)

    def save(self, commit=True):
        instance = super().save(commit)

        self.update_profile(instance)

        return instance


class ClientRoleInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            user = form.cleaned_data.get('user')
            try:
                if user:
                    user.profile
            except AttributeError:
                raise ValidationError(f'User {user} has more than one role.')


class CandidateImportForm(ImportForm):
    organization = forms.ModelChoiceField(queryset=Client.objects.all(), required=True)


class CandidateConfirmImportForm(ConfirmImportForm):
    organization = forms.ModelChoiceField(queryset=Client.objects.all(), required=True)
