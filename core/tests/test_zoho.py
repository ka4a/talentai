from unittest.mock import patch

from django.utils import translation
from django.test import TestCase
from rest_framework.serializers import ValidationError

from core import fixtures as f
from core.zoho import ZohoApiError
from core.zoho import ZohoImportError, import_zoho_candidate, ZohoNoCandidate
from core.zoho import get_candidate_id_from_zoho_url, to_candidate_data
from core.utils import get_country_code_by_name


class ToCandidateDataTestCase(TestCase):
    def test_convert(self):
        zoho_data = [
            {'val': 'CANDIDATEID', 'content': '123'},
            {'val': 'First Name', 'content': 'John'},
            {'val': 'Last Name', 'content': 'Smith'},
            {'val': 'Email', 'content': 'john@localhost'},
            {'val': 'Country', 'content': 'Japan'},
            {'val': 'City', 'content': 'Tokyo'},
            {'val': '', 'content': ''},
        ]
        with translation.override('en'):
            current_country = get_country_code_by_name('Japan')
        expected_candidate_data = {
            'zoho_id': '123',
            'zoho_data': zoho_data,
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john@localhost',
            'current_city': 'Tokyo',
            'current_country': current_country,
        }

        self.assertDictEqual(to_candidate_data(zoho_data), expected_candidate_data)

    def test_ignore_null_values(self):
        """Should ignore 'null' values."""
        zoho_data = [
            {'content': 'null', 'val': 'Email'},
        ]

        self.assertDictEqual(to_candidate_data(zoho_data), {'zoho_data': zoho_data})

    def test_ignore_invalid_values(self):
        """Should ignore invalid values."""
        zoho_data = [
            {'content': 'invalid email', 'val': 'Email'},
        ]

        self.assertDictEqual(to_candidate_data(zoho_data), {'zoho_data': zoho_data})

    def test_duplicates(self):
        """Should ignore duplicates."""
        # different labels can be mapped to same candidate field
        zoho_data = [
            {'content': 'a', 'val': 'First Name'},
            {'content': 'b', 'val': 'First Name'},
        ]

        self.assertDictEqual(
            to_candidate_data(zoho_data), {'zoho_data': zoho_data, 'first_name': 'a'}
        )


class GetCandidateIdFromZohoUrlTestCase(TestCase):
    def test_parse_url(self):
        self.assertEqual(
            get_candidate_id_from_zoho_url(
                'https://recruit.zoho.com/recruit/EntityInfo.do?'
                'module=Candidates&id=123'
            ),
            '123',
        )

    def test_parse_url_edit_page(self):
        self.assertEqual(
            get_candidate_id_from_zoho_url(
                'https://recruit.zoho.com/recruit/EditEntity.do?'
                'module=Candidates&id=123'
            ),
            '123',
        )

    def test_parse_url_no_protocol(self):
        self.assertEqual(
            get_candidate_id_from_zoho_url(
                'recruit.zoho.com/recruit/EditEntity.do?' 'module=Candidates&id=123'
            ),
            '123',
        )

    def test_parse_invalid_id(self):
        with self.assertRaises(ValueError):
            get_candidate_id_from_zoho_url(
                'https://recruit.zoho.com/recruit/EntityInfo.do?'
                'module=Candidates&id=123v'
            )

    def test_parse_no_id(self):
        with self.assertRaises(ValueError):
            get_candidate_id_from_zoho_url(
                'https://recruit.zoho.com/recruit/EntityInfo.do?'
                'module=Candidates&id='
            )

    def test_parse_incorrect_module(self):
        with self.assertRaises(ValueError):
            get_candidate_id_from_zoho_url(
                'https://recruit.zoho.com/recruit/EntityInfo.do?'
                'module=Clients&id=123'
            )

    def test_parse_invalid_path(self):
        with self.assertRaises(ValueError):
            get_candidate_id_from_zoho_url(
                'https://recruit.zoho.com/recruit/ShowTab.do?module=Candidates'
            )

    def test_parse_no_url(self):
        with self.assertRaises(ValueError):
            get_candidate_id_from_zoho_url('')


def get_date_filters(data, field):
    value = data.get(field)

    if value is None:
        return dict()

    parts = value.split('-')
    if len(parts) < 2:
        return dict()

    return {f'{field}__month': parts[0], f'{field}__year': parts[1]}


class ImportZohoCandidateTestCase(TestCase):
    ZOHO_DATA_DUMMY = [{'val': 'dummy', 'content': '1'}]

    def setUp(self):
        self.agency = f.create_agency()
        self.agency.zoho_auth_token = 'a' * 32
        self.agency_administrator = f.create_agency_administrator(self.agency)

        self.client_obj = f.create_client()
        self.client_obj.zoho_auth_token = 'a' * 32
        self.client_admin = f.create_client_administrator(self.client_obj)

    @patch('core.zoho.get_zoho_candidate_data')
    @patch('core.zoho.get_zoho_candidate_tabular_data')
    def check_import(
        self, user, get_zoho_candidate_tabular_data_mock, get_zoho_candidate_data_mock
    ):
        zoho_id = '123'
        get_zoho_candidate_data_mock.return_value = {
            **f.DEFAULT_CANDIDATE,
            'zoho_id': zoho_id,
            'zoho_data': self.ZOHO_DATA_DUMMY,
        }

        get_zoho_candidate_tabular_data_mock.return_value = f.ZOHO_TABULAR_DATA

        candidate = import_zoho_candidate(user, zoho_id)

        get_zoho_candidate_data_mock.assert_called_once_with(
            user.profile.org.zoho_auth_token, zoho_id,
        )

        get_zoho_candidate_tabular_data_mock.assert_called_once_with(
            user.profile.org.zoho_auth_token, zoho_id,
        )

        candidate_data = {
            'organization': candidate.organization,
            'first_name': candidate.first_name,
            'zoho_id': candidate.zoho_id,
            'zoho_data': candidate.zoho_data,
        }
        expected_data = {
            'organization': user.profile.org,
            'first_name': f.DEFAULT_CANDIDATE['first_name'],
            'zoho_id': '123',
            'zoho_data': self.ZOHO_DATA_DUMMY,
        }

        for data in f.ZOHO_TABULAR_DATA['education_details']:
            self.assertEqual(
                len(
                    candidate.education_details.filter(
                        institute=data['institute'],
                        department=data['department'],
                        degree=data['degree'],
                        currently_pursuing=data.get('currently_pursuing', False),
                        **get_date_filters(data, 'date_start'),
                        **get_date_filters(data, 'date_end'),
                    )
                ),
                1,
                msg='Education details not found',
            )

        for data in f.ZOHO_TABULAR_DATA['experience_details']:
            self.assertEqual(
                len(
                    candidate.experience_details.filter(
                        occupation=data['occupation'],
                        company=data['company'],
                        summary=data['summary'],
                        currently_pursuing=data.get('currently_pursuing', False),
                        **get_date_filters(data, 'date_start'),
                        **get_date_filters(data, 'date_end'),
                    )
                ),
                1,
                msg='Experince details not found',
            )

        self.assertDictEqual(candidate_data, expected_data)

    def test_import_agency(self):
        self.check_import(self.agency_administrator)

    def test_import_client(self):
        self.check_import(self.client_admin)

    @patch('core.zoho.get_zoho_candidate_data')
    def test_no_candidate(self, get_zoho_candidate_data_mock):
        get_zoho_candidate_data_mock.side_effect = ZohoNoCandidate({})

        with self.assertRaises(ZohoImportError):
            import_zoho_candidate(self.agency_administrator, '123')

    @patch('core.zoho.get_zoho_candidate_data')
    def test_client_error(self, get_zoho_candidate_data_mock):
        get_zoho_candidate_data_mock.side_effect = ZohoApiError({})

        with self.assertRaises(ZohoImportError):
            import_zoho_candidate(self.agency_administrator, '123')

    @patch('core.zoho.get_zoho_candidate_tabular_data')
    @patch('core.zoho.get_zoho_candidate_data')
    def test_import_already_exists(
        self, get_zoho_candidate_data_mock, get_zoho_candidate_tabular_data
    ):
        """Should raise a ValidationError"""
        candidate = f.create_candidate(self.agency)
        candidate.zoho_id = '123'
        candidate.save()

        get_zoho_candidate_data_mock.return_value = {
            **f.DEFAULT_CANDIDATE,
            'linkedin_url': candidate.linkedin_url,
            'zoho_id': '123',
            'zoho_data': {'dummy': 1},
        }

        get_zoho_candidate_tabular_data.return_value = {
            'education_details': [],
            'experience_details': [],
        }

        with self.assertRaises(ValidationError) as e:
            import_zoho_candidate(self.agency_administrator, '123')
            self.assertTrue('zoho_id' in e.message_dict)

    @patch('core.zoho.get_zoho_candidate_tabular_data')
    @patch('core.zoho.get_zoho_candidate_data')
    def test_already_exists_linkedin(
        self, get_zoho_candidate_data_mock, get_zoho_candidate_tabular_data
    ):
        """Should raise a ValidationError"""
        candidate = f.create_candidate(self.agency)
        candidate.linkedin_url = 'https://www.linkedin.com/in/someslug/'
        candidate.save()

        get_zoho_candidate_data_mock.return_value = {
            **f.DEFAULT_CANDIDATE,
            'linkedin_url': candidate.linkedin_url,
            'zoho_id': '123',
            'zoho_data': {'dummy': 1},
        }

        get_zoho_candidate_tabular_data.return_value = {
            'education_details': [],
            'experience_details': [],
        }

        with self.assertRaises(ValidationError) as e:
            import_zoho_candidate(self.agency_administrator, '123')
            self.assertEqual('linkedin_url' in e.message_dict)
