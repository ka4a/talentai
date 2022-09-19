# -*- coding: utf-8 -*-
import io
import logging
import uuid
import re
from urllib.parse import urlsplit, parse_qs
from itertools import count
import requests

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import (
    Candidate,
    Language,
    EducationDetail,
    ExperienceDetail,
)
from core.utils import map_data, get_country_code_by_name


class ZohoApiError(Exception):
    def __init__(self, body):
        self.body = body

    def __str__(self):
        return repr(self.body)

    def __repr__(self):
        return 'ZohoApiError(body={!r})'.format(self.body)


class ZohoInvalidToken(ZohoApiError):
    pass


class ZohoNoCandidate(ZohoApiError):
    pass


class ZohoRecruitClient:
    base_url = 'https://recruit.zoho.com/recruit/private/json/'

    def __init__(self, auth_token, module='Candidates'):
        self.auth_token = auth_token
        self.logger = logging.getLogger('core.zoho')
        self.api_version = '4'
        self.module = module

    def request(self, method, path, params=None, raw=False, **kwargs):
        params = params or {}
        params = {
            'scope': 'recruitapi',
            'version': self.api_version,
            'authtoken': self.auth_token,
            **params,
        }

        r = requests.request(method, self.base_url + path, params=params, **kwargs)

        self.logger.debug(u'%r - %r: %r', r.request, r, r.text)

        if raw:
            return r

        response = r.json()
        error = response.get('response', {}).get('error')

        if error and error['code'] == '4834':
            raise ZohoInvalidToken(response)

        return response

    def get_fields(self):
        response = self.request('POST', f'{self.module}/getFields')
        return response

    def get_related_records(self, record_id):
        response = self.request(
            'POST',
            'Attachments/getRelatedRecords',
            params={'parentModule': self.module, 'newFormat': '1', 'id': record_id},
        )['response']

        if 'nodata' in response:
            return []

        r = response['result']['Attachments']['row']

        if isinstance(r, dict):
            return [r['FL']]

        return [i['FL'] for i in r]

    def download_file(self, attach_id):
        response = self.request(
            'POST', f'{self.module}/downloadFile', params={'id': attach_id}, raw=True
        )

        if 'Content-Disposition' not in response.headers:
            raise ZohoNoCandidate(body=response.json())

        cd = response.headers['Content-Disposition']

        if cd.startswith("attachment;filename*=UTF-8''"):
            filename = cd.split("filename*=UTF-8''", 1)[-1]
        else:
            filename = 'file'

        return response.content, filename

    def get_records(self, params=None, endpoint='getRecords'):
        params = params or {}
        response = self.request('POST', f'{self.module}/{endpoint}', params)['response']
        if 'result' in response:
            return response['result'][self.module]['row']

        return []

    def get_all_records(self, params=None, endpoint='getRecords', index_range=100):
        params = params if params else {}

        for page in count(start=1):
            from_index = 1 + index_range * (page - 1)
            to_index = index_range * page
            data = self.get_records(
                {'fromIndex': from_index, 'toIndex': to_index, **params}, endpoint
            )
            if not data:
                break

            yield from data

    def get_record_by_id(self, id_):
        response = self.request(
            'POST', f'{self.module}/getRecordById', params={'newFormat': '2', 'id': id_}
        ).get('response')

        if not response or 'nodata' in response:
            raise ZohoNoCandidate(body=response)

        return response['result'][self.module]['row']['FL']

    def get_tabular_records(self, id_, record_types=None):
        tabular_names = ','.join(record_types) if record_types else ''
        response = self.request(
            'POST',
            f'{self.module}/getTabularRecords',
            params={'newFormat': '2', 'id': id_, 'tabularNames': f'({tabular_names})'},
        )

        if not response or 'nodata' in response:
            raise ZohoNoCandidate(body=response)

        return response

    def download_photo(self, id_):
        response = self.request(
            'POST', f'{self.module}/downloadPhoto', params={'id': id_}, raw=True
        )

        if 'Content-Disposition' not in response.headers:
            raise ZohoNoCandidate(body=response.json())

        content_type = response.headers['Content-Type']
        clean_content_type = None

        if content_type.startswith('image/'):
            clean_content_type = content_type.split(';', 1)[0]

        return response.content, clean_content_type


def validate_zoho_auth_token(auth_token):
    try:
        ZohoRecruitClient(auth_token).get_records()
        return True
    except ZohoInvalidToken:
        return False


FIELDS_MAPPING = {
    'zoho_id': 'CANDIDATEID',
    'first_name': 'First Name',
    'first_name_kanji': '名',
    'last_name': 'Last Name',
    'last_name_kanji': '姓',
    'email': 'Email',
    'phone': ('Phone', 'Mobile'),
    'website_url': 'Website',
    'current_company': 'Current Employer',
    'current_position': 'Job Title',
    'potential_locations': 'Potential Locations',
    'twitter_url': 'Twitter',
    'linkedin_url': 'Linkedin',
    'source_details': 'Source',
    'salary': ('Current Salary', 'Expected Salary'),
    'reason_for_job_changes': 'Salary Breakdown',
}

TABULAR_FIELD_CONTENT_MAPPING = {
    'Educational Details': {
        'institute': 'Institute / School',
        'department': 'Major / Department',
        'degree': 'Degree',
        'date_start': 'Duration_From',
        'date_end': 'Duration_To',
        'currently_pursuing': 'Currently pursuing',
    },
    'Experience Details': {
        'occupation': 'Occupation / Title',
        'company': 'Company',
        'summary': 'Summary',
        'date_start': 'Work Duration_From',
        'date_end': 'Work Duration_To',
        'currently_pursuing': 'I currently work here',
    },
}

TABULAR_FIELDS_MAPPING = {
    'education_details': 'Educational Details',
    'experience_details': 'Experience Details',
}


def zoho_data_to_dict(data, content_field='content'):
    result = dict()
    for field in data:
        key = field['val']
        value = field.get(content_field, 'null')

        if value == 'null' or key in result:
            continue

        if value == 'true':
            value = True
        if value == 'false':
            value = False

        result[key] = value
    return result


def zoho_tabular_data_to_dict(raw_data, content_map, type_map, module='Candidates'):
    data = zoho_data_to_dict(raw_data['response']['result'][module]['FL'], 'TR')

    for group_name, _map in content_map.items():
        new_list = []
        group_data = data.get(group_name, [])

        if not isinstance(group_data, list):
            group_data = [group_data]

        for item in group_data:
            new_list.append(map_data(zoho_data_to_dict(item['TL']), _map))

        data[group_name] = new_list

    return map_data(data, type_map)


def to_candidate_data(
    zoho_data, photo=None, photo_content_type=None, files=None,
):
    if files is None:
        files = []

    candidate_data = {
        'zoho_data': zoho_data,
    }

    fields_data = zoho_data_to_dict(zoho_data)
    candidate_data.update(map_data(fields_data, FIELDS_MAPPING))

    if candidate_data.get('source_details', None):
        candidate_data['source'] = 'Job Boards'

    if 'Country' in fields_data:
        candidate_data['current_country'] = get_country_code_by_name(
            fields_data['Country']
        )

    if 'City' in fields_data:
        country = fields_data.get('Country')
        current_country = candidate_data.get('current_country')
        if country and not current_country:
            candidate_data['current_city'] = f'{fields_data["City"]} / {country}'
        else:
            candidate_data['current_city'] = fields_data["City"]

    # remove invalid fields data
    try:
        Candidate(**candidate_data).clean_fields()
    except ValidationError as e:
        invalid_fields = e.message_dict.keys()
        for i in invalid_fields:
            candidate_data.pop(i, None)

    if photo:
        photo_f = io.BytesIO(photo)
        candidate_data['photo'] = InMemoryUploadedFile(
            photo_f,
            'ImageField',
            f'{uuid.uuid4()}.jpg',
            photo_content_type,
            photo_f.getbuffer().nbytes,
            None,
        )

    for f_data, filename in files[:1]:  # TODO: multiple files
        file_f = io.BytesIO(f_data)
        candidate_data['resume'] = InMemoryUploadedFile(
            file_f, 'FileField', filename, None, file_f.getbuffer().nbytes, None
        )

    return candidate_data


def get_candidate_id_from_zoho_url(url):
    """Return Zoho candidate ID from URL:
    https://recruit.zoho.com/recruit/EntityInfo.do?module=Candidates&id=123
    """
    if not url:
        raise ValueError('No URL')

    parsed_url = urlsplit(url.strip())

    urlstart = ''.join(filter(None, [parsed_url.hostname, parsed_url.path]))

    valid_url = (
        urlstart == 'recruit.zoho.com/recruit/EntityInfo.do'
        or urlstart == 'recruit.zoho.com/recruit/EditEntity.do'
    )
    if not valid_url:
        raise ValueError('Should start with "recruit.zoho.com/recruit/EntityInfo.do"')

    query_data = parse_qs(parsed_url.query)

    if query_data.get('module') != ['Candidates']:
        raise ValueError('Should be candidate URL')

    id_list = query_data.get('id')

    if not id_list:
        raise ValueError('No ID in URL')

    try:
        int(id_list[0])
    except ValueError:
        raise ValueError('Invalid ID in URL')

    return id_list[0]


class ZohoData:
    LANGUAGE_LEVEL_MAPPING = {'en': 'English Level', 'ja': 'Japanese Level'}

    LANGUAGE_LEVEL_VALUES = {
        'Basic': 0,
        'Conversational': 1,
        'Business': 2,
        'Fluent': 3,
        'Native': 4,
    }

    def __init__(self, data):
        self.data = data

    def __getitem__(self, item):
        for field in self.data:
            if field['val'] == item:
                if field['content'] == 'null':
                    return None
                return field['content']
        return None

    def get_language_level(self, key):
        zoho_key = self.LANGUAGE_LEVEL_MAPPING.get(key, None)
        zoho_language_level = self[zoho_key]
        if zoho_language_level is None:
            return None
        return self.LANGUAGE_LEVEL_VALUES.get(zoho_language_level, None)

    def language_iter(self):
        for key in self.LANGUAGE_LEVEL_MAPPING:
            level = self.get_language_level(key)
            if level is not None:
                yield key, level


def get_zoho_candidate_tabular_data(auth_token, candidate_zoho_id):
    c = ZohoRecruitClient(auth_token)
    tabular_data = c.get_tabular_records(
        candidate_zoho_id, ['Experience Details', 'Educational Details']
    )

    return zoho_tabular_data_to_dict(
        tabular_data, TABULAR_FIELD_CONTENT_MAPPING, TABULAR_FIELDS_MAPPING
    )


def get_zoho_candidate_data(auth_token, candidate_zoho_id):
    c = ZohoRecruitClient(auth_token)
    zoho_candidate_data = c.get_record_by_id(candidate_zoho_id)

    try:
        photo, photo_content_type = c.download_photo(candidate_zoho_id)
    except ZohoApiError:
        photo, photo_content_type = None, None

    files = []

    file_records = c.get_related_records(candidate_zoho_id)
    for file_record in file_records:
        file_id = None
        file_category = None

        for i in file_record:
            if i['val'] == 'id':
                file_id = i['content']
            elif i['val'] == 'Category':
                file_category = i['content']

        if not file_id:
            logging.error('No file id?: {!r}'.format(file_record))
            continue

        # TODO: download all files, when multiple files would be
        # allowed for candidate
        if file_category == 'Resume' and not files:
            files.append(c.download_file(file_id))

    return to_candidate_data(zoho_candidate_data, photo, photo_content_type, files,)


class ZohoImportError(Exception):
    def __init__(self, message):
        self.message = message


zoho_date_re = re.compile(r'(?P<month>\d{2})-(?P<year>\d{4})$')


def convert_zoho_date_to_iso(value):
    match = zoho_date_re.match(value)
    if match:
        return '{year}-{month}-01'.format(**match.groupdict())


def get_zoho_candidate(organization, candidate_zoho_id):
    try:
        candidate_data = get_zoho_candidate_data(
            organization.zoho_auth_token, candidate_zoho_id
        )
        tabular_data = get_zoho_candidate_tabular_data(
            organization.zoho_auth_token, candidate_zoho_id
        )
    except ZohoNoCandidate:
        raise ZohoImportError(_('Could not find this candidate.'))
    except (ZohoApiError, requests.exceptions.RequestException):
        raise ZohoImportError(_('Could not load candidate data from Zoho.'))

    for sub_list in tabular_data.values():
        for item in sub_list:
            for date_key in ('date_start', 'date_end'):
                if item.get(date_key) is not None:
                    item[date_key] = convert_zoho_date_to_iso(item[date_key])
                else:
                    item[date_key] = None

    candidate_data.update(tabular_data)

    return candidate_data


def save_zoho_candidate(validated_data, user):
    organization = user.profile.org
    candidate_data = dict(validated_data)
    if not candidate_data.get('email'):
        candidate_data['email'] = ''

    tabular_data = {
        key: candidate_data.pop(key)
        for key in ('education_details', 'experience_details')
    }

    zoho_data = ZohoData(candidate_data['zoho_data'])

    try:
        candidate = Candidate.objects.create(
            organization=organization,
            employment_status='fulltime',
            owner=user,
            created_by=user,
            **candidate_data,
        )
    except ValidationError as e:
        raise serializers.ValidationError(e.message_dict)

    note = zoho_data['Consultant Notes']
    if note:
        candidate.set_note(organization, note)

    for lang, level in zoho_data.language_iter():
        candidate.languages.add(Language.objects.get(language=lang, level=level,))

    related_models = (
        ('education_details', EducationDetail),
        ('experience_details', ExperienceDetail),
    )

    # creating instances of related Models
    for related_field, Model in related_models:
        for params in tabular_data[related_field]:
            Model.objects.create(candidate=candidate, **params)

    return candidate


def import_zoho_candidate(user, candidate_zoho_id):
    candidate_data = get_zoho_candidate(user.profile.org, candidate_zoho_id)
    candidate = save_zoho_candidate(candidate_data, user)

    return candidate
