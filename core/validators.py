from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from rest_framework import serializers

from core.utils.common import get_nested_item


def unique_entries(value):
    if len(value) != len(set(value)):
        raise serializers.ValidationError('Duplicate values in field.')


def get_field_source(field, serializer):
    """
    field - as declared in Serializer's Meta
    """
    try:
        return serializer.fields[field].source
    except KeyError as invalid_field:
        raise KeyError(
            f'`{field}` is not a declared field on the serializer'
        ) from invalid_field


class SpecialCharacterValidator:
    def __init__(self, num_special_chars=1):
        self.num_special_chars = num_special_chars

    def count_special_chars(self, value):
        special_char = 0
        for i in range(0, len(value)):
            if value[i].isalpha() or value[i].isdigit():
                continue
            else:
                special_char += 1
        return special_char

    def validate(self, password, user=None):
        if self.count_special_chars(password) < self.num_special_chars:
            raise ValidationError(
                _(
                    "This password must contain at least %(num_special_chars)d special character/s."
                ),
                code='password_lacks_special_chars',
                params={'num_special_chars': self.num_special_chars},
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(num_special_chars)d special character/s."
            % {'num_special_chars': self.num_special_chars}
        )


class ModeRequirementValidator:
    message = _('This field is required')

    def __init__(self, mode_field, field_cases, message=None):
        self.mode_field = mode_field
        self.field_cases = field_cases
        self.message = message or self.message

    def __call__(self, attrs):
        mode = attrs[self.mode_field]
        for field, field_mode in self.field_cases.items():
            if mode == field_mode:
                field_value = attrs.get(field)
                if field_value is None:
                    raise serializers.ValidationError(
                        {field: [self.message]}, code='required'
                    )


class ModeRequireFieldsValidator:
    """
    Make field required if certain choice value is passed
    """

    message = _('This field is required')
    requires_context = True

    def __init__(self, mode_field, required_fields_by_mode, message=None):
        """
        :param mode_field: Choice field
        :param required_fields_by_mode: Map of required fields to the choice field values in which case listed fields
        are required, example
          {
            'choice_a': ['field_1', 'field_2'],
            'choice_b': ['field_3']
          }
        :param message: Message that would be shown, if required field is missing
        """
        self.mode_field = mode_field
        self.required_fields_by_mode = required_fields_by_mode
        self.message = message or self.message

    def __call__(self, attrs, serializer):
        mode_field_source = get_field_source(self.mode_field, serializer)
        mode = get_nested_item(attrs, mode_field_source, default=None)
        if not mode:
            return
        for field in self.required_fields_by_mode.get(mode, []):
            field_source = get_field_source(field, serializer)
            if not get_nested_item(attrs, field_source, default=None):
                raise serializers.ValidationError(
                    {field: [self.message]}, code='required'
                )


class ModeChoicesValidator:
    messages = {
        'invalid_choice': _('"{choice}" is not a valid choice.'),
        'no_choices': _('No choices available for "{mode}".'),
        'mode_required': _('This field is required.'),
    }
    requires_context = True

    def __init__(self, field, mode_field, mode_choices, mode_is_required=True):
        self.field = field
        self.mode_field = mode_field
        self.mode_choices = mode_choices
        self.mode_is_required = mode_is_required

    def __call__(self, attrs, serializer):
        field_source = get_field_source(self.field, serializer)
        choice = get_nested_item(attrs, field_source, default=None)
        mode_field_source = get_field_source(self.mode_field, serializer)
        mode = get_nested_item(attrs, mode_field_source, default=None)
        if not self.mode_is_required and not mode:
            return
        if not mode:
            raise serializers.ValidationError(
                {self.mode_field: [self.messages['mode_required']]}
            )
        choices = self.mode_choices.get(mode)
        if choices is None:
            return
        if not choices:
            raise serializers.ValidationError(
                {self.field: [self.messages['no_choices']]}
            )
        if choice not in choices:
            raise serializers.ValidationError(
                {self.field: [self.messages['invalid_choice'].format(choice=choice)]}
            )


class RequireOneOfValidator:
    messages = {
        'required': _('This field is required'),
        'exclusive': _('Only one field must be set: {}'),
    }

    def __init__(self, fields, exclusive=False, messages=None):
        self.fields = fields
        self.exclusive = exclusive
        self.messages = messages or self.messages

    def __call__(self, attrs):
        errors = dict()
        num_fields_set = 0
        for field in self.fields:
            field_value = attrs.get(field, None)

            if field_value:
                num_fields_set += 1
            else:
                errors[field] = [self.messages['required']]

        if self.exclusive and num_fields_set > 1:
            raise serializers.ValidationError(
                {'non_field_errors': [self.messages['exclusive'].format(self.fields)]}
            )
        if errors and not num_fields_set:
            raise serializers.ValidationError(errors)


class RequireIfValidator:
    messages = {
        'required': _('This field is required.'),
        'blank': _('This field can\'t be blank.'),
    }

    def __init__(self, field, flag_field):
        self.field = field
        self.flag_field = flag_field

    def __call__(self, attrs):
        field_value = attrs.get(self.field)

        if not attrs.get(self.flag_field, False):
            return

        if field_value is None:
            self.fail('required')

        if field_value == '':
            self.fail('blank')

    def fail(self, message_name):
        raise serializers.ValidationError({self.field: [self.messages[message_name]]})


class FieldsSumValidator:
    message = _('Sum of fields must be equal to {total}')

    def __init__(self, total, fields, message=None):
        self.total = total
        self.fields = fields

        self.message = message or self.message

    def __call__(self, attrs):
        total = sum(attrs[field] for field in self.fields if field in attrs)

        if total != self.total:
            raise serializers.ValidationError(
                {
                    field: [self.message.format(total=self.total)]
                    for field in self.fields
                }
            )


class SplitHasUserValidator:
    message = _('Non-empty split requires user to be selected.')

    def __init__(self, user, split, message=None):
        self.user = user
        self.split = split

        self.message = message or self.message

    def __call__(self, attrs):
        if attrs[self.split]:
            if not attrs[self.user]:
                raise serializers.ValidationError({self.user: [self.message]})
