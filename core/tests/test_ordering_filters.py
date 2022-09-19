from unittest.mock import patch

from django.db.models.query import QuerySet
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.views import APIView

from talentai.ordering_filters import (
    unlock_request_query_params,
    mutate_ordering_fields,
    CamelCaseOrderingFilter,
)


class OrderingFilterTests(APITestCase):
    """Tests related to ordering filter."""

    def test_unlock_request_query_params_unlocked(self):
        """Param _mutable is True in context manager."""
        request = APIView().initialize_request(APIRequestFactory().get('/'))

        with unlock_request_query_params(request):
            self.assertTrue(request.query_params._mutable)

    def test_unlock_request_query_params_locked(self):
        """Param _mutable is False when exited context manager."""
        request = APIView().initialize_request(APIRequestFactory().get('/'))

        with unlock_request_query_params(request):
            pass
        self.assertFalse(request.query_params._mutable)

    def test_unlock_request_query_params_preserved(self):
        """Param _mutable preserved when exited context manager."""
        request = APIView().initialize_request(APIRequestFactory().get('/'))

        request.query_params._mutable = True

        with unlock_request_query_params(request):
            pass
        self.assertTrue(request.query_params._mutable)

    def test_mutate_ordering_fields_not_in_mapping(self):
        """Value unchanged if not in mapping."""
        value = 'test'
        mapping = {'other': ['one']}

        result = mutate_ordering_fields(value, mapping)
        self.assertEqual(result, value)

    def test_mutate_ordering_fields_not_in_mapping_minus_preserved(self):
        """Value minus symbol preserved when not in mapping."""
        value = '-test'
        mapping = {'other': ['one']}

        result = mutate_ordering_fields(value, mapping)
        self.assertEqual(result, value)

    def test_mutate_ordering_fields_not_in_mapping_plus_preserved(self):
        """Value plus symbol preserved when not in mapping."""
        value = '+test'
        mapping = {'other': ['one']}

        result = mutate_ordering_fields(value, mapping)
        self.assertEqual(result, value)

    def test_mutate_ordering_fields_single_value_in_mapping(self):
        """Should replace the value."""
        value = 'test'
        mapping = {'test': ['one']}

        result = mutate_ordering_fields(value, mapping)
        self.assertEqual(result, 'one')

    def test_mutate_ordering_fields_single_value_symbol_preserved(self):
        """Should preserve the symbol when the value has changed."""
        value = '-test'
        mapping = {'test': ['one']}

        result = mutate_ordering_fields(value, mapping)
        self.assertEqual(result, '-one')

    def test_mutate_ordering_fields_list_in_mappings(self):
        """Should replace the value with comma-separated values from list."""
        value = 'test'
        mapping = {'test': ['one', 'two']}

        result = mutate_ordering_fields(value, mapping)
        self.assertEqual(result, 'one,two')

    def test_mutate_ordering_fields_list_symbol_preserved(self):
        """Each value from the list gets its copy of the symbol."""
        value = '-test'
        mapping = {'test': ['one', 'two']}

        result = mutate_ordering_fields(value, mapping)
        self.assertEqual(result, '-one,-two')

    @patch('talentai.ordering_filters.mutate_ordering_fields')
    def test_camel_case_ordering_filter_without_ordering(self, mock):
        """Mutation method not called if no ordering in params."""
        request = APIView().initialize_request(APIRequestFactory().get('/'))

        CamelCaseOrderingFilter().get_ordering(request, QuerySet(), APIView())
        mock.assert_not_called()

    @patch('rest_framework.filters.OrderingFilter.get_ordering')
    @patch('talentai.ordering_filters.mutate_ordering_fields')
    def test_camel_case_ordering_filter_with_ordering(self, mutate_mock, ordering_mock):
        """Mutation method called if ordering in params."""
        mutate_mock.return_value = 'test'
        ordering_mock.return_value = None

        request = APIView().initialize_request(
            APIRequestFactory().get('/?ordering=test')
        )

        CamelCaseOrderingFilter().get_ordering(request, QuerySet(), APIView())
        mutate_mock.assert_called()

    @patch('rest_framework.filters.OrderingFilter.get_ordering')
    def test_camel_case_ordering_filter_camelized(self, ordering_mock):
        """Mutation method called if ordering in params."""
        ordering_mock.return_value = None

        request = APIView().initialize_request(
            APIRequestFactory().get('/?ordering=testTest')
        )

        CamelCaseOrderingFilter().get_ordering(request, QuerySet(), APIView())
        self.assertEqual(request.query_params.get('ordering'), 'test_test')

    @patch('rest_framework.filters.OrderingFilter.get_ordering')
    def test_camel_case_ordering_filter_mutated(self, ordering_mock):
        """Ordering is mutated according to the mapping."""
        ordering_mock.return_value = None

        request = APIView().initialize_request(
            APIRequestFactory().get('/?ordering=testTest')
        )

        view = APIView()
        view.ordering_fields_mapping = {'test_test': ['one_val', 'two_val']}

        CamelCaseOrderingFilter().get_ordering(request, QuerySet(), view)
        self.assertEqual(request.query_params.get('ordering'), 'one_val,two_val')

    @patch('rest_framework.filters.OrderingFilter.get_ordering')
    def test_camel_case_ordering_filter_symbol_preserved(self, ordering_mock):
        """Symbol preserved when passed an ordering value with a symbol.."""
        ordering_mock.return_value = None

        request = APIView().initialize_request(
            APIRequestFactory().get('/?ordering=-testTest')
        )

        view = APIView()
        view.ordering_fields_mapping = {'test_test': ['one_val', 'two_val']}

        CamelCaseOrderingFilter().get_ordering(request, QuerySet(), view)
        self.assertEqual(request.query_params.get('ordering'), '-one_val,-two_val')
