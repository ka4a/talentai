import jwt
from datetime import datetime
from rest_framework.test import APITestCase
from django.conf import settings

from core.fixtures import create_user
from core.tests.generic_response_assertions import GenericResponseAssertionSet


class ZendeskSSOTests(APITestCase):
    """Tests of Zendesk SSO endpoint"""

    def setUp(self):
        self.user = create_user(
            email='karamazov@example.com', first_name='Fyodor', last_name='Karamazov'
        )
        self.assert_response = GenericResponseAssertionSet(self)

    def test_not_authenticated(self):
        self.assert_response.not_authenticated('get', 'zendesk-sso-jwt')

    def test_ok(self):
        self.client.force_login(self.user)

        data = self.assert_response.ok('get', 'zendesk-sso-jwt').json()

        unix_now = int(datetime.utcnow().timestamp())
        token_payload = jwt.decode(
            jwt=data['token'],
            key=settings.ZENDESK_SSO_SECRET,
            algorithms=settings.ZENDESK_SSO_JWT_ENCODING,
        )

        self.assertEqual(token_payload['name'], 'Fyodor Karamazov')
        self.assertEqual(token_payload['email'], 'karamazov@example.com')
        self.assertEqual(token_payload['external_id'], str(self.user.id))
        self.assertLessEqual(unix_now - token_payload['iat'], 1000)
        self.assertIsNotNone(token_payload['jti'])
