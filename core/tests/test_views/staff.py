from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from djangorestframework_camel_case.util import camelize
from rest_framework.test import APITestCase

from core import fixtures as f, serializers as s
from core.factories import (
    ClientFactory,
    ClientInternalRecruiterFactory,
    ClientAdministratorFactory,
    ClientStandardUserFactory,
)
from core.tests.generic_response_assertions import GenericResponseAssertionSet


class StaffTests(APITestCase):
    """Tests for Staff related endpoints."""

    def setUp(self):
        """Create necessary objects during initialization."""
        super().setUp()

        client = ClientFactory.create()
        self.client_admin = client.primary_contact
        client.assign_administrator(self.client_admin)

        self.client_org = client

        self.recruiter = ClientInternalRecruiterFactory.create(client=client).user

        self.assert_response = GenericResponseAssertionSet(self)

        self.client.force_login(self.client_admin)

    def get_users(self, sources=None, role=None):
        if not sources or 'current_client' in sources:
            if role == 'admin' or not role:
                yield self.client_admin

            if role == 'regular' or not role:
                yield self.recruiter
                yield ClientStandardUserFactory.create(client=self.client_org).user

        if not sources or 'other_client' in sources:
            client = ClientFactory.create(unique=True)

            if role == 'admin':
                yield ClientAdministratorFactory.create(client=client).user

            if role == 'regular':
                factories = [ClientInternalRecruiterFactory, ClientStandardUserFactory]

                for factory in factories:
                    yield factory.create(client=client).user

    def test_get_client_staff(self):
        """Should return details of an Staff member."""
        self.assert_response.ok(
            'get',
            'staff-detail',
            self.recruiter.pk,
            expected_data=camelize(s.RetrieveStaffSerializer(self.recruiter).data),
        )

    def test_get_client_staff_list(self):
        """Should return a list of Staff members."""
        data = self.assert_response.ok(
            'get', 'staff-list', None, {'ordering': 'id'}
        ).json()

        self.assertEqual(
            data['results'],
            camelize(
                s.StaffSerializer([self.client_admin, self.recruiter], many=True).data
            ),
        )

    UPDATE_PAYLOAD = {
        'first_name': 'Frank',
        'last_name': 'Herbert',
        'email': 'frank.herbert@example.com',
        'country': 'us',
        'locale': 'en',
    }

    def test_update_client_staff(self):
        """Should update Staff member."""
        data = self.UPDATE_PAYLOAD
        expected_data = {
            **data,
            'email': self.recruiter.email,
        }
        expected_response_data = camelize(expected_data)
        expected_response_data.pop('email')

        self.assert_response.ok(
            'put', 'staff-detail', self.recruiter.pk, data, expected_response_data
        )

        self.recruiter.refresh_from_db()

        for field in expected_data:
            self.assertEqual(getattr(self.recruiter, field), expected_data[field])

    def test_patch_bad_field(self):
        data = {
            'first_name': '',
        }

        response_data = self.assert_response.bad_request(
            'patch', 'staff-detail', self.recruiter.pk, data
        ).json()
        self.assertTrue('firstName' in response_data)

    def test_upload_photo(self):
        self.assert_response.ok(
            'post',
            'staff-upload-photo',
            self.recruiter.pk,
            format='multipart',
            data={'file': SimpleUploadedFile('img.jpg', f.get_jpeg_image_content())},
        )

        self.recruiter.refresh_from_db()

        self.assertIsNotNone(self.recruiter.photo)

    @staticmethod
    def add_photo(user):
        user.photo.save('img.jpg', ContentFile(f.get_jpeg_image_content()))

    def test_download_photo(self):
        self.add_photo(self.recruiter)
        self.recruiter.save()
        self.assert_response.ok('get', 'staff-photo', self.recruiter.pk)

    def test_delete_photo(self):
        self.add_photo(self.recruiter)

        self.assert_response.ok('delete', 'staff-photo', self.recruiter.pk)

        self.recruiter.refresh_from_db()

    def test_delete_photo_not_allowed(self):
        self.assert_response.for_users(self.get_users(role='regular')).no_permission(
            'delete', 'staff-photo', self.client_admin.pk,
        )

    def test_delete_photo_not_found(self):
        self.assert_response.for_users(
            self.get_users(['other_client'], 'admin')
        ).not_found(
            'delete', 'staff-photo', self.client_admin.pk,
        )

    def test_upload_photo_not_found(self):
        self.assert_response.for_users(
            self.get_users(['other_client'], 'admin')
        ).not_found(
            'post',
            'staff-upload-photo',
            self.client_admin.pk,
            format='multipart',
            data={'file': SimpleUploadedFile('img.jpg', f.get_jpeg_image_content())},
        )

    def test_download_photo_not_found(self):
        self.assert_response.for_users(self.get_users(['other_client'])).not_found(
            'get', 'staff-photo', self.client_admin.pk,
        )

    def test_upload_photo_no_permission(self):
        self.assert_response.for_users(self.get_users(role='regular'),).no_permission(
            'post', 'staff-upload-photo', self.client_admin.pk,
        )

    def test_update_no_permission(self):
        self.assert_response.for_users(self.get_users(role='regular'),).no_permission(
            'patch', 'staff-detail', self.client_admin.pk, self.UPDATE_PAYLOAD,
        )

    def test_update_not_found(self):
        self.assert_response.for_users(
            self.get_users(['other_client'], 'admin'),
        ).not_found(
            'patch', 'staff-detail', self.client_admin.pk, self.UPDATE_PAYLOAD,
        )

    def test_retrieve_ok(self):
        self.assert_response.for_users(self.get_users(['current_client']),).ok(
            'get', 'staff-detail', self.client_admin.pk,
        )

    def test_retrieve_not_found(self):
        self.assert_response.for_users(self.get_users(['other_client']),).ok(
            'get', 'staff-detail', self.client_admin.pk,
        )
