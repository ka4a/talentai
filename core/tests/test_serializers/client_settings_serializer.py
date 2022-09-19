from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from core import fixtures as f, serializers as s, models as m


class ClientSettingsSerializerTests(TestCase):
    api_factory = APIRequestFactory()

    def setUp(self):
        self.admin = f.create_user(email='a@client1.net')
        self.client_org = f.create_client(
            'client1',
            self.admin,
            name_ja='クライアント1',
            country='jp',
            website='http://client1.com',
        )
        self.client_org.logo = SimpleUploadedFile(
            'logo.jpg', f.get_jpeg_image_content(), 'image/jpeg'
        )
        self.client_org.save()

        self.functions = [
            m.Function.objects.create(title=title)
            for title in ('Optimisation', 'Progress')
        ]

    def test_update_success(self):
        request = self.api_factory.post('/')
        request.user = self.admin

        function_ids = [item.id for item in self.functions]

        serializer = s.ClientSettingsSerializer(
            instance=self.client_org,
            context={'request': request},
            data={
                'name': 'Client2',
                'name_ja': 'Client2_ja',
                'website': 'http://client2.io',
                'country': 'ru',
                'function_focus': function_ids,
                'logo': None,
                'career_site_slug': None,
                'is_career_site_enabled': False,
            },
        )

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        serializer.save()

        self.client_org.refresh_from_db()

        self.assertEqual(self.client_org.name, 'Client2')
        self.assertEqual(
            self.client_org.function_focus.filter(id__in=function_ids).count(),
            len(function_ids),
        )

    def test_serialize_success(self):
        for function_focus in self.functions:
            self.client_org.function_focus.add(function_focus)

        serializer = s.ClientSettingsSerializer(
            instance=self.client_org, context=dict(request=self.api_factory.get('/')),
        )

        function_ids = [item.id for item in self.functions]

        self.assertDictEqual(
            serializer.data,
            {
                'name': 'client1',
                'name_ja': 'クライアント1',
                'website': 'http://client1.com',
                'country': 'jp',
                'function_focus': function_ids,
                'logo': 'http://testserver{logo_url}'.format(
                    logo_url=self.client_org.logo.url,
                ),
                'career_site_slug': None,
                'is_career_site_enabled': False,
            },
        )
