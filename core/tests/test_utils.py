from collections import OrderedDict

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import QuerySet
from django.db.models.fields.files import FieldFile
from django.test import TestCase
from unittest.mock import patch

from ..models import User
from core.utils import (
    RequestInContextMissing,
    compare_model_dicts,
    LinkedinProfile,
    require_request,
    fix_for_yasg,
    camelize_str,
    send_email,
    parse_linkedin_slug,
    format_serializer_as_response,
    pick,
)
from core.utils.file import get_filename_from_path
from core.utils.view import create_file_download_response
from core.fixtures import get_jpeg_image_content


class Pick(TestCase):
    def test_dict_key_subset(self):
        self.assertEqual(
            {'a': 1, 'b': 2},
            pick({'a': 1, 'b': 2, 'c': 3}, {'a': 'alpha', 'b': 'bravo'}),
        )

    def test_dict_not_key_subset(self):
        self.assertEqual(
            {'a': 1, 'b': 2},
            pick({'a': 1, 'b': 2, 'c': 3}, {'a': 'alpha', 'b': 'bravo', 'e': 'echo'}),
        )


class CamelizeStr(TestCase):
    def test_word(self):
        self.assertEqual(camelize_str('word'), 'word')

    def test_2_words(self):
        self.assertEqual(camelize_str('two_words'), 'twoWords')

    def test_2_dash(self):
        self.assertEqual(camelize_str('two__dash_string'), 'two_DashString')


class FakeViewSet:
    queryset = User.objects.all()

    def __init__(self, swagger_fake_view):
        self.swagger_fake_view = swagger_fake_view
        self.called = False

    @fix_for_yasg
    def get_queryset(self):
        self.called = True


class FixForYasgTestCase(TestCase):
    def test_fixed(self):
        fake_view = FakeViewSet(True)
        r = fake_view.get_queryset()

        self.assertFalse(fake_view.called)
        self.assertTrue(isinstance(r, QuerySet))

    def test_bypass(self):
        fake_view = FakeViewSet(False)
        fake_view.get_queryset()

        self.assertTrue(fake_view.called)


class FakeSerializer:
    def __init__(self, add_request):
        if add_request:
            self.context = {'request': 'whatever'}
        else:
            self.context = {}

    @require_request
    def method_with_request_required(self):
        pass


class RequireRequestTestCase(TestCase):
    def test_request_not_provided(self):
        with self.assertRaises(RequestInContextMissing):
            FakeSerializer(False).method_with_request_required()

    def test_request_provided(self):
        try:
            FakeSerializer(True).method_with_request_required()
        except RequestInContextMissing:
            self.fail('ValueError should not be raised')


class UtilCompareModelDictsTestCase(TestCase):
    def test_compare_model_dicts_compare(self):
        first = {'a': 1, 'b': 'old'}
        second = {'a': 2, 'b': 'new'}

        self.assertEqual(
            compare_model_dicts(first, second, compare=['a', 'b']),
            {'a': {'from': 1, 'to': 2}, 'b': {'from': 'old', 'to': 'new'}},
        )

    def test_compare_model_dicts_compare_same(self):
        same = {'a': 'same'}

        self.assertEqual(compare_model_dicts(same, same, compare=['a']), {})

    def test_compare_model_dicts_compare_ignored(self):
        first = {'a': 1, 'b': 1}
        second = {'a': 2, 'b': 2}

        self.assertEqual(
            compare_model_dicts(first, second, compare=['a']),
            {'a': {'from': 1, 'to': 2},},
        )

    def test_compare_model_dicts_compare_as_set(self):
        first = {'a': [1, 2, 3]}
        second = {'a': [2, 3, 4]}

        self.assertEqual(
            compare_model_dicts(first, second, compare_as_set=['a']),
            {'a': {'removed': {1}, 'added': {4}},},
        )

    def test_compare_model_dicts_compare_as_set_same(self):
        same = {'a': [1, 2, 3]}

        self.assertEqual(compare_model_dicts(same, same, compare_as_set=['a']), {})

    def test_compare_model_dicts_compare_by_matching_key(self):
        first = {
            'a': [
                {'id': 1, 'b': 'hello'},
                {'id': 2, 'b': 'same'},
                {'id': 3, 'b': 'removed'},
            ]
        }
        second = {
            'a': [
                {'id': 1, 'b': 'world'},
                {'id': 2, 'b': 'same'},
                {'id': 4, 'b': 'new'},
            ]
        }

        self.assertEqual(
            compare_model_dicts(
                first, second, compare_by_matching_key=[('a', 'id', {'compare': ['b']})]
            ),
            {
                'a': {
                    1: {'b': {'from': 'hello', 'to': 'world'}},
                    'removed': [{'id': 3, 'b': 'removed'}],
                    'added': [{'id': 4, 'b': 'new'}],
                },
            },
        )

    def test_compare_model_dicts_compare_by_matching_key_same(self):
        same = {'a': [{'id': 1, 'b': 'hello'}]}

        self.assertEqual(
            compare_model_dicts(
                same, same, compare_by_matching_key=[('a', 'id', {'compare': ['b']})]
            ),
            {},
        )


class UtilParseLinkedinSlugTestCase(TestCase):
    """Tests for parse_linedin_slug function only."""

    @staticmethod
    def parse_linkedin_slug(url):
        return parse_linkedin_slug(url)

    def test_parse_url(self):
        """Linkedin slug parsed."""
        self.assertEqual(
            self.parse_linkedin_slug('https://linkedin.com/in/some-slug/'), 'some-slug'
        )

    def test_parse_url_with_www(self):
        """Linkedin slug with www parsed."""
        self.assertEqual(
            self.parse_linkedin_slug('https://www.linkedin.com/in/some-slug/'),
            'some-slug',
        )

    def test_parse_url_with_ja(self):
        """Linkedin slug with ja subdomain parsed."""
        self.assertEqual(
            self.parse_linkedin_slug('https://ja.linkedin.com/in/some-slug/'),
            'some-slug',
        )

    def test_parse_url_without_trailing_slash(self):
        """Linkedin slug without trailing slash parsed."""
        self.assertEqual(
            self.parse_linkedin_slug('https://www.linkedin.com/in/some-slug'),
            'some-slug',
        )

    def test_parse_url_with_get_parameters(self):
        """Linkedin slug with get parameters parsed."""
        self.assertEqual(
            self.parse_linkedin_slug('https://www.linkedin.com/in/some-slug/?qwe=1'),
            'some-slug',
        )

    def test_parse_url_with_extra_path_segment(self):
        """Linkedin slug with extra path segment parsed."""
        self.assertEqual(
            self.parse_linkedin_slug('https://www.linkedin.com/in/some-slug/qwe/'),
            'some-slug',
        )

    def test_parse_url_with_tilda(self):
        """Linkedin slug with tilda parsed."""
        self.assertEqual(
            self.parse_linkedin_slug('https://www.linkedin.com/in/~some-slug/'),
            '~some-slug',
        )

    def test_parse_url_encoded(self):
        """Linkedin slug with encoded username parsed."""
        self.assertEqual(
            self.parse_linkedin_slug('https://www.linkedin.com/in/yo%EF%BC%88lo/'),
            'yo（lo',
        )

    def test_parse_url_not_encoded(self):
        """Linkedin slug with space parsed."""
        self.assertEqual(
            self.parse_linkedin_slug('https://www.linkedin.com/in/yo（lo/'), 'yo（lo'
        )

    def test_parse_no_url(self):
        """None returned when None passed."""
        self.assertEqual(self.parse_linkedin_slug(None), None)

    def test_parse_no_url_str(self):
        """None returned when empty string passed."""
        self.assertEqual(self.parse_linkedin_slug(''), None)

    def test_parse_invalid_domain(self):
        """None returned when invalid domain passed."""
        self.assertEqual(
            self.parse_linkedin_slug('https://localhost/in/some-slug/qwe/'), None
        )

    def test_parse_no_slug(self):
        """None returned if no slug in url."""
        self.assertEqual(self.parse_linkedin_slug('https://www.linkedin.com/in/'), None)

    def test_parse_no_slug1(self):
        """None returned if no slug and two trailing slashes in url."""
        self.assertEqual(
            self.parse_linkedin_slug('https://www.linkedin.com/in//'), None
        )

    def test_parse_no_path(self):
        """None returned if a linkedin link to not a user passed."""
        self.assertEqual(self.parse_linkedin_slug('https://www.linkedin.com/'), None)


class LinkedInProfileTestCase(UtilParseLinkedinSlugTestCase):
    @staticmethod
    def parse_linkedin_slug(url):
        profile = LinkedinProfile({'contact_info': {'linked_in': url,}})

        return profile.slug

    def test_candidate_data(self):

        profile = LinkedinProfile(
            {
                'name': 'John Smith',
                'headline': 'Position',
                'company': 'Company',
                'city': 'Location',
                'original': 2,
                'contact_info': {
                    'linked_in': 'LinkedinURL',
                    'email': 'Email',
                    'twitter': ['Twitter'],
                },
            }
        )

        expected_data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'current_position': 'Position',
            'current_company': 'Company',
            'current_city': 'Location',
            'linkedin_url': 'LinkedinURL',
            'original_id': 2,
            'email': 'Email',
            'twitter_url': 'Twitter',
        }
        self.assertEqual(profile.candidate_data, expected_data)

    @staticmethod
    def try_split_name(name):
        profile = LinkedinProfile({'name': name})
        data = profile.candidate_data
        return [data['first_name'], data['last_name']]

    def test_name_first_and_last_name(self):
        self.assertEqual(self.try_split_name('John Smith'), ['John', 'Smith'])

    def test_name_nickname(self):
        """Probably shouldn't attempt to find first name and last name."""
        self.assertEqual(
            self.try_split_name('John "h4x0r" Smith'), ['John "h4x0r" Smith', '']
        )


class SendEmailTestCase(TestCase):
    @patch('core.tasks.send_email.delay')
    def check_send(self, send_email_mock, *args, is_html=False, body):
        additional_kwargs = {'extension': 'html'} if is_html else dict()
        send_email(
            to='fake@test.net',
            folder='send_email_test',
            context={'name': 'test', 'word': 'hello'},
            **additional_kwargs,
        )

        body_key = 'html_body' if is_html else 'body'

        send_email_mock.assert_called_once_with(
            to=['fake@test.net'],
            subject='Im test, and i want to say hello\n',
            **{body_key: body},
        )

    def test_send_txt(self):
        self.check_send(body='Im test, and i want to say hello\n')

    def test_send_html(self):
        self.check_send(is_html=True, body='<p>Im test, and i want to say hello</p>\n')


class MockSerializer:
    def __init__(self, data):
        self.data = data


class FormatSerializerAsResponseTestCase(TestCase):
    def assert_is_dict(self, expected, key_str=''):
        msg = f'result{key_str} is not unordered dict'
        self.assertEqual(type(expected), dict, msg)

    def test_single(self):

        expected = {
            'id': 1,
            'name': 'test',
            'parent': {'id': 2, 'name': 'parent'},
            'oddity': {'type': 'unordered'},
            'children': [{'id': 3, 'name': 'unordered'}, {'id': 4, 'name': 'ordered'}],
        }

        result = format_serializer_as_response(
            MockSerializer(
                OrderedDict(
                    (
                        ('id', 1),
                        ('name', 'test'),
                        ('parent', OrderedDict((('id', 2), ('name', 'parent'),))),
                        ('oddity', {'type': 'unordered'}),
                        (
                            'children',
                            [
                                {'id': 3, 'name': 'unordered'},
                                OrderedDict((('id', 4), ('name', 'ordered'),)),
                            ],
                        ),
                    )
                )
            )
        )

        self.assertEqual(expected, result)

        # dict and ordered dict are considered equal,
        # so they should be checked
        self.assert_is_dict(result)
        self.assert_is_dict(result['parent'], "['parent']")
        self.assert_is_dict(result['oddity'], "['oddity']")
        self.assert_is_dict(result['children'][0], "['children'][0]")
        self.assert_is_dict(result['children'][1], "['children'][1]")

    def test_multiple(self):
        expected = [{'id': 3, 'name': 'unordered'}, {'id': 4, 'name': 'ordered'}]
        result = format_serializer_as_response(
            MockSerializer(
                [
                    {'id': 3, 'name': 'unordered'},
                    OrderedDict((('id', 4), ('name', 'ordered'),)),
                ]
            )
        )

        self.assertEqual(expected, result)

        self.assert_is_dict(result[0], '[0]')
        self.assert_is_dict(result[1], '[1]')


class TestGetFilenameFromPath(TestCase):
    def test_nested_path(self):
        self.assertEqual(
            get_filename_from_path('/path/to/file/filename.txt',), 'filename.txt'
        )

    def test_plain_path(self):

        self.assertEqual(get_filename_from_path('filename.txt'), 'filename.txt')
