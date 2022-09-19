import binascii
import pytz
import random
import re
import string

from datetime import date
from functools import wraps
from urllib.parse import urlsplit, unquote
from uuid import uuid4

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Case, When, Value, BooleanField
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone, translation
from rest_framework import exceptions
from djangorestframework_camel_case.util import (
    camelize_re,
    underscore_to_camel,
    camelize,
)

from core.constants import NOT_SET
from core import tasks
from core import datasets


def camelize_str(key):
    return re.sub(camelize_re, underscore_to_camel, key)


def fix_for_yasg(f):
    """Fix get_queryset for django-yasg. Requires queryset to be defined."""

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()
        return f(self, *args, **kwargs)

    return wrapper


class RequestInContextMissing(Exception):
    def __init__(self):
        super().__init__('Request in context is required')


def require_user_profile(f):
    """Fix get_queryset for requests by non-profiled users"""

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        user = self.request.user
        if not hasattr(user, 'profile') or user.profile is None:
            raise exceptions.PermissionDenied()
        return f(self, *args, **kwargs)

    return wrapper


def require_request(f):
    """Require request in serializer context."""

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if 'request' not in self.context:
            raise RequestInContextMissing()
        return f(self, *args, **kwargs)

    return wrapper


def has_profile(user, specific_profile=None):
    if not specific_profile:
        return hasattr(user, 'profile') and user.profile is not None

    return hasattr(user, 'profile') and hasattr(user.profile, specific_profile)


def get_trans(language, message):
    with translation.override(language):
        return translation.gettext(message)


def set_drf_sensitive_post_parameters(request, value='__ALL__'):
    setattr(request._request, 'sensitive_post_parameters', value)


def convert_request_meta_to_dict(request):
    return {
        key: value
        for key, value in request.META.items()
        if key.startswith('HTTP_') and 'CSRF' not in key and 'COOKIE' not in key
    }


def compare_dict_fields(old, new, fields):
    changed_fields = {}

    for f in fields:
        if old[f] != new[f]:
            changed_fields[f] = {'from': old[f], 'to': new[f]}

    return changed_fields


def compare_dict_fields_as_set(old, new, fields):
    changed_fields = {}

    for field in fields:
        old_set = set(old[field])
        new_set = set(new[field])

        added = new_set - old_set
        removed = old_set - new_set

        result = {}

        if added:
            result['added'] = added

        if removed:
            result['removed'] = removed

        if result:
            changed_fields[field] = result

    return changed_fields


def compare_dict_fields_by_matching_key(old, new, fields):
    changed_fields = {}

    for f, compare_key, compare_kwargs in fields:
        old_dict = {data[compare_key]: data for data in old[f]}
        new_dict = {data[compare_key]: data for data in new[f]}

        result = {}

        added_keys = new_dict.keys() - old_dict.keys()
        removed_keys = old_dict.keys() - new_dict.keys()

        if added_keys:
            result['added'] = [new_dict[k] for k in added_keys]

        if removed_keys:
            result['removed'] = [old_dict[k] for k in removed_keys]

        same_keys = old_dict.keys() & new_dict.keys()
        for k in same_keys:
            c = compare_model_dicts(old_dict[k], new_dict[k], **compare_kwargs)
            if c:
                result[k] = c

        if result:
            changed_fields[f] = result

    return changed_fields


def compare_model_dicts(
    old, new, compare=None, compare_as_set=None, compare_by_matching_key=None
):

    changed_fields = {}

    if compare:
        changed_fields.update(compare_dict_fields(old, new, compare))

    if compare_as_set:
        changed_fields.update(compare_dict_fields_as_set(old, new, compare_as_set))

    if compare_by_matching_key:
        changed_fields.update(
            compare_dict_fields_by_matching_key(old, new, compare_by_matching_key)
        )

    return changed_fields


def parse_linkedin_slug(url):
    """Parse linkedin username, return None if no slug found."""
    parsed_url = urlsplit(url)

    valid_url = parsed_url.hostname and (
        parsed_url.hostname == 'linkedin.com'
        or parsed_url.hostname.endswith('.linkedin.com')
    )
    if not valid_url:
        return None

    split_path = parsed_url.path.split('/')

    try:
        if split_path[1] == 'in' and split_path[2]:
            return unquote(split_path[2]).strip()
    except IndexError:
        return None


def send_email(to, folder, context, extension='txt', attachments=None):
    send_email_kwargs = {
        'to': [to],
        'subject': render_to_string(f'{folder}/subject.txt', context,),
    }
    body = render_to_string(f'{folder}/body.{extension}', context,)

    if attachments:
        send_email_kwargs['attachments'] = attachments

    if extension == 'html':
        send_email_kwargs['html_body'] = body
    else:
        send_email_kwargs['body'] = body

    tasks.send_email.delay(**send_email_kwargs)


class Base64Photo:
    DATA_URI_PHOTO_PREFIXES = {
        'data:image/jpeg;base64': 'jpg',
        'data:image/png;base64': 'png',
    }

    def __init__(self, base64):
        self.info = None
        self.file = None
        self.ext = None
        self.filename = None

        self.info, base64_data = base64.split(',', 1)
        self.ext = self.DATA_URI_PHOTO_PREFIXES.get(self.info)

        if not self.ext:
            return

        self.filename = f'{uuid4()}.{self.ext}'

        try:
            self.file = ContentFile(binascii.a2b_base64(base64_data))
        except binascii.Error:
            pass


def map_key_iterator(map_):
    for new_key, key, in map_.items():

        if type(key) in (list, tuple):
            for item in key:
                yield new_key, item,

        else:
            yield new_key, key


def map_data(data, map_):
    result = dict()

    for new_key, key in map_key_iterator(map_):

        if key not in data:
            continue

        if new_key in result:
            continue

        result[new_key] = data[key]

    return result


EMPTY_TUPLE = tuple()


class LinkedinProfile:
    education_map = {
        'institute': 'school',
        'degree': 'degree',
        'department': 'fos',
        'date_start': 'date_start',
        'date_end': 'date_end',
        'currently_pursuing': 'currently_pursuing',
    }
    experience_map = {
        'occupation': 'title',
        'company': 'org',
        'summary': 'desc',
        'date_start': 'date_start',
        'date_end': 'date_end',
        'currently_pursuing': 'currently_pursuing',
    }

    def __init__(self, data):
        self.data = data
        self._photo = None
        self._contact_data = None
        self._candidate_data = None
        self._slug = None
        self._url = None
        self.proposal = data.get('proposal')

    def _map_list(self, key, map_):
        _list = self.data.get(key, EMPTY_TUPLE)
        for item in _list:
            yield map_data(item, map_)

    @property
    def educational_details(self):
        result = self._map_list('education', self.education_map)

        return result

    @property
    def experience_details(self):
        result = self._map_list('experience', self.experience_map)

        return result

    @property
    def url(self):
        if self._url is not None:
            return self._url
        try:
            url = self.data['contact_info']['linked_in']
        except KeyError:
            return None

        if url is None:
            return None

        self._url = url.split('?', 1)[0].split('#', 1)[0]
        return self._url

    @property
    def slug(self):
        if self._slug is not None:
            return self._slug

        self._slug = parse_linkedin_slug(self.url)

        return self._slug

    @property
    def photo(self):
        if self._photo is not None:
            return self._photo

        data = self.data.get('photo_base64', None)
        if data:
            self._photo = Base64Photo(data)

        return self._photo

    @property
    def contact_data(self):
        if self._contact_data is not None:
            return self.contact_data

        self._contact_data = {}
        data = self.data.get('contact_info', {})

        if data.get('email'):
            self._contact_data['email'] = data['email']

        if data.get('twitter'):
            self._contact_data['twitter_url'] = data['twitter'][0]

        self._contact_data['linkedin_url'] = self.url

        # dunno how to fit into PhoneNumberField (no country code)
        # if data['phone']:
        #     self._contact_data['phone'] = data['phone'][0]

        for website in data.get('website', []):
            if 'github.com/' in website and not self._contact_data.get('github_url'):
                self._contact_data['github_url'] = website
            elif not self._contact_data.get('website_url'):
                self._contact_data['website_url'] = website

        return self._contact_data

    def _try_split_name(self):
        name = self.data.get('name', '')
        name_parts = name.strip().split(' ')

        if len(name_parts) == 2:
            return name_parts

        return [name, '']

    @property
    def candidate_data(self):
        if self._candidate_data is not None:
            return self._candidate_data

        first_name, last_name = self._try_split_name()

        self._candidate_data = {
            'first_name': first_name,
            'last_name': last_name,
            'current_position': self.data.get('headline', ''),
            'current_company': self.data.get('company', ''),
            'current_city': self.data.get('city', ''),
            'original_id': self.data.get('original', None),
            **self.contact_data,
        }

        return self._candidate_data


def poly_relation_filter(id_key, content_type_key, obj):
    return Q(
        **{id_key: obj.id, content_type_key: ContentType.objects.get_for_model(obj)}
    )


def org_filter(org):
    return poly_relation_filter('org_id', 'org_content_type', org)


def deep_convert_ordered_dict_to_dict(root):
    if isinstance(root, dict):
        return {key: deep_convert_ordered_dict_to_dict(root[key]) for key in root}

    if isinstance(root, (list, tuple)):
        return [deep_convert_ordered_dict_to_dict(item) for item in root]

    return root


def format_serializer_as_response(serializer):
    return deep_convert_ordered_dict_to_dict(camelize(serializer.data))


def get_unique_emails_filter(value):
    return Q(email=value) & ~Q(email='') & ~Q(email=None) | Q(
        secondary_email=value
    ) & ~Q(secondary_email='') & ~Q(secondary_email=None)


def get_user_org(profile):
    if not profile:
        return None, None

    org_content_type = ContentType.objects.get_for_model(profile.org)
    org_id = profile.org.id

    return org_content_type, org_id


def get_country_list(locale=None):
    locale = locale if locale else translation.get_language()
    for possible_locale in [locale, 'en']:
        try:
            name_key = f'name_{locale}'
            return [
                {'code': c['code'], 'name': c[name_key]} for c in datasets.countries
            ]
        except KeyError:
            pass


def get_country_name(code, locale=None):
    for country in get_country_list(locale):
        if country['code'] == code:
            return country['name']
    return None


def get_country_code_by_name(country_name='', locale=None):
    for country in get_country_list(locale):
        if country_name.strip().lower() == country['name'].strip().lower():
            return country['code']

    return ''


def has_researcher_feature(profile):
    return hasattr(profile, 'agency') and getattr(
        profile.org, 'enable_researcher_field_feature'
    )


def filter_out_serializer_fields(obj, fields):
    return {key: value for key, value in obj.items() if key not in fields}


def pick(dictionary, relevant_keys):
    return {key: dictionary[key] for key in dictionary if key in relevant_keys}


class SerializerErrorsMock:
    def __init__(self, serializer_class, error_messages=None):
        serializer = serializer_class()
        self.declared_fields = serializer.get_fields()
        self.default_error_messages = serializer_class.default_error_messages
        self.messages = error_messages or dict()

    def add_custom_error(self, field_name, error_message):
        if field_name not in self.messages:
            self.messages[field_name] = []

        self.messages[field_name].append(error_message)

    def add_field_error(self, field_name, error_name, *args, **kwargs):
        self.add_custom_error(
            field_name,
            self.declared_fields[field_name]
            .error_messages[error_name]
            .format(*args, **kwargs),
        )

    def add_non_field_error(self, error_name):
        self.add_custom_error('nonFieldErrors', self.default_error_messages[error_name])


def get_bool_annotation(condition):
    return Case(
        When(condition=condition, then=Value(True)),
        default=Value(False),
        output_field=BooleanField(),
    )


def calculate_age(born_date):
    today = date.today()
    return (
        today.year
        - born_date.year
        - ((today.month, today.day) < (born_date.month, born_date.day))
    )


def create_invoice_number(last_order, date):
    return '{order}{date:%Y%m}'.format(order=last_order + 1, date=date)


def gen_random_string(length=16):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))


def datetime_str(datetime_raw=None, user=None):
    # TODO(ZOO-1073): use proper timezones
    LOCALE_TZ_MAPPING = {
        'en': pytz.timezone('UTC'),
        'ja': pytz.timezone('Asia/Tokyo'),
    }
    local_timezone = LOCALE_TZ_MAPPING['ja']
    _datetime = datetime_raw or timezone.now()
    return f'{timezone.localtime(_datetime, local_timezone).strftime("%c")} ({local_timezone})'


def pop(d, key, **kwargs):
    """
    Return tuple of (d[key] or default, isPopped)
    kwargs[default] to prevent raising keyerror
    """
    try:
        return (d.pop(key), True)
    except KeyError:
        if 'default' in kwargs:
            return (kwargs['default'], False)
        else:
            raise


def get(d, key, **kwargs):
    """
    Return tuple of (d[key] or default, isPopped)
    kwargs[default] to prevent raising keyerror
    """
    try:
        return (d[key], True)
    except KeyError:
        if 'default' in kwargs:
            return (kwargs['default'], False)
        else:
            raise


def get_nested_item(dictionary, path, default=NOT_SET):
    """
    Given:
    d = {'a': {'b': {'c': 'value'}}}
    path = "a.b.c"
    Returns:
    'value'
    Pass default inhibit error
    """
    child = dictionary
    try:
        for key in path.split('.'):
            child = child[key]
    except (AttributeError, KeyError) as failed_access:
        if default is NOT_SET:
            raise KeyError(
                f'Tried accessing `{path}` from `{dictionary}`'
            ) from failed_access
        else:
            return default

    return child
