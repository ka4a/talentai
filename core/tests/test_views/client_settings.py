from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from core.tests.generic_response_assertions import GenericResponseAssertionSet
from core.models import Function
import core.fixtures as f


class ClientSettingsTest(APITestCase):
    def setUp(self):
        self.assert_response = GenericResponseAssertionSet(self)
        self.client_admin = f.create_user(email='admin@client1.com')

        self.client_org = f.create_client(
            name='client1',
            name_ja='client1_ja',
            website='https://client1.com',
            country='jp',
            primary_contact=self.client_admin,
        )
        self.client_org.logo = SimpleUploadedFile(
            'logo.jpg', f.get_jpeg_image_content(), 'image/jpeg'
        )
        self.client_org.save()
        self.client_org.assign_administrator(self.client_admin)

        self.functions = [
            Function.objects.create(title=title)
            for title in ['electronics', 'software']
        ]

    def test_get_success(self):
        expected_data = dict(
            name='client1',
            nameJa='client1_ja',
            website='https://client1.com',
            country='jp',
            functionFocus=[],
            logo='http://testserver{logo_url}'.format(
                logo_url=self.client_org.logo.url,
            ),
            careerSiteSlug=None,
            isCareerSiteEnabled=False,
        )
        self.client.force_login(self.client_admin)
        self.assert_response.ok('get', 'client-settings', expected_data=expected_data)

    def test_get_not_client_admin(self):
        user = f.create_user()
        self.client_org.assign_standard_user(user)

        self.client.force_login(user)
        self.assert_response.no_permission('get', 'client-settings')

    def test_patch_success(self):
        function_ids = [item.id for item in self.functions]
        data = dict(website='https://client2.com', functionFocus=function_ids,)

        self.client.force_login(self.client_admin)
        self.assert_response.ok('patch', 'client-settings', data=data)

        self.client_org.refresh_from_db()

        count = self.client_org.function_focus.filter(id__in=function_ids).count()
        self.assertEqual(count, len(self.functions))
        self.client_org.website = data['website']

    def test_patch_not_client_admin(self):
        user = f.create_user()
        self.client_org.assign_standard_user(user)

        data = dict(website='https://client2.com', functionFocus=[],)
        self.client.force_login(user)
        self.assert_response.no_permission('patch', 'client-settings', data=data)
