"""Tests related to filters of the core Django app."""
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.test import APITestCase

from core import fixtures as f
from core.filters import AgencyFilter, ProposalCommentFilterSet
from core.models import Agency, ProposalComment

User = get_user_model()


class AgencyTests(APITestCase):
    """Tests related to the AgencyFilter."""

    def setUp(self):
        """Create related objects during test class initialization."""
        super().setUp()
        self.agency = f.create_agency()
        self.agency_other = f.create_agency()
        self.client_obj = f.create_client()
        f.create_contract(
            self.agency, self.client_obj,
        )

    def test_working_with_filter_recruiter(self):
        """Should return unchanged queryset passed by Recruiter."""
        user = f.create_user('test@test.com', 'password')
        self.agency.assign_recruiter(user)

        request = Request(HttpRequest())
        request.user = user
        filter = AgencyFilter()
        filter.request = request

        queryset = Agency.objects
        result = filter.working_with_filter(queryset, None, None)
        self.assertEqual(set(result.all()), set(queryset.all()))

    def test_working_with_filter_talent_associate(self):
        """Should return Agencies his Client is working with."""
        user = f.create_user('test@test.com', 'password')
        self.client_obj.assign_administrator(user)

        request = Request(HttpRequest())
        request.user = user
        filter = AgencyFilter()
        filter.request = request

        result = filter.working_with_filter(Agency.objects, None, None)
        self.assertEqual(
            set(result.all()), set(Agency.objects.filter(pk=self.agency.pk)),
        )

    def test_working_with_filter_hiring_manager(self):
        """Should return Agencies his Client is working with."""
        user = f.create_user('test@test.com', 'password')
        self.client_obj.assign_standard_user(user)

        request = Request(HttpRequest())
        request.user = user
        filter = AgencyFilter()
        filter.request = request

        result = filter.working_with_filter(Agency.objects, None, None)
        self.assertEqual(
            set(result.all()), set(Agency.objects.filter(pk=self.agency.pk)),
        )


class ProposalCommentTests(APITestCase):
    """Tests for ProposalCommentFilterSet."""

    def setUp(self):
        """Create related objects during test class initialization."""
        super().setUp()

        client = f.create_client()
        agency = f.create_agency()
        self.client_admin = f.create_client_administrator(client)

        self.proposal = f.create_proposal(
            f.create_job(client), f.create_candidate(agency), self.client_admin,
        )

        self.comment = f.create_proposal_comment(
            self.client_admin, self.proposal, public=False, system=False
        )
        self.comment_public = f.create_proposal_comment(
            self.client_admin, self.proposal, public=True, system=False
        )
        self.comment_system = f.create_proposal_comment(
            self.client_admin, self.proposal, public=False, system=True
        )
        self.comment_public_system = f.create_proposal_comment(
            self.client_admin, self.proposal, public=True, system=True
        )

    def test_public_filter_true(self):
        """Contains public Proposal comments."""
        f = ProposalCommentFilterSet()

        result = f.public_filter(ProposalComment.objects, None, True)
        self.assertEqual(
            set(result.all()), {self.comment_public, self.comment_public_system}
        )

    def test_public_filter_false(self):
        """Contains non public Proposal comments and public system comments."""
        f = ProposalCommentFilterSet()

        result = f.public_filter(ProposalComment.objects, None, False)
        self.assertEqual(
            set(result.all()),
            {self.comment, self.comment_system, self.comment_public_system},
        )
