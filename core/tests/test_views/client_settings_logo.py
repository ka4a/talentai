from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from core.tests.generic_response_assertions import GenericResponseAssertionSet
import core.fixtures as f


class ClientSettingsTest(APITestCase):
    def setUp(self):
        self.assert_response = GenericResponseAssertionSet(self)
        self.client_admin = f.create_user(email='admin@client1.com')

        self.client_org = f.create_client()
        self.client_org.save()
        self.client_org.assign_administrator(self.client_admin)

    @staticmethod
    def create_logo():
        return SimpleUploadedFile('logo.jpg', f.get_jpeg_image_content())

    def create_post_payload(self):
        return {'file': self.create_logo()}

    def test_post_success(self):
        self.client.force_login(self.client_admin)
        self.assert_response.ok(
            'post',
            'client-settings-logo',
            data=self.create_post_payload(),
            format='multipart',
        )

        self.client_org.refresh_from_db()
        self.assertTrue(self.client_org.logo)

    def test_post_not_client_admin(self):
        user = f.create_user()
        self.client_org.assign_standard_user(user)

        self.client.force_login(user)

        self.assert_response.no_permission(
            'post',
            'client-settings-logo',
            data=self.create_post_payload(),
            format='multipart',
        )

    def test_get_success(self):
        self.client.force_login(self.client_admin)

        self.client_org.logo = self.create_logo()
        self.client_org.save()

        self.assert_response.ok('get', 'client-settings-logo')

    def test_get_not_client_admin(self):
        user = f.create_user()
        self.client_org.assign_standard_user(user)
        self.client.force_login(user)

        self.client_org.logo = self.create_logo()
        self.client_org.save()

        self.assert_response.no_permission('get', 'client-settings-logo')

    def test_delete_success(self):
        self.client.force_login(self.client_admin)

        self.client_org.logo = self.create_logo()
        self.client_org.save()

        self.assert_response.ok('delete', 'client-settings-logo')

        self.client_org.refresh_from_db()
        self.assertFalse(self.client_org.logo)

    def test_delete_not_client_admin(self):
        user = f.create_user()
        self.client_org.assign_standard_user(user)
        self.client.force_login(user)

        self.client_org.logo = self.create_logo()
        self.client_org.save()

        self.assert_response.no_permission('delete', 'client-settings-logo')
