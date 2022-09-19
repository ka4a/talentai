import time

from django.conf import settings
from django.urls.base import reverse
from rest_framework.test import APITestCase

from core import factories as fa


class SessionTests(APITestCase):
    def test_login_zk_user(self):
        password = 'thisistestingpassword!'
        ca = fa.ClientAdministratorFactory(user__password=password)
        data = {'email': ca.user.email, 'password': password}

        self.assertEqual(
            self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE
        )
        url = reverse('user-login')
        response = self.client.post(url, data, format='json')

        self.assertEqual(
            self.client.session.get_expiry_age(), settings.SESSION_NON_ADMIN_COOKIE_AGE
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ca.user.pk, response.data['id'])

    def test_login_staff_user(self):
        password = 'thisistestingpassword!'
        user = fa.UserFactory(password=password, is_staff=True)
        data = {'email': user.email, 'password': password}

        self.assertEqual(
            self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE
        )
        url = reverse('user-login')
        response = self.client.post(url, data, format='json')

        self.assertEqual(
            self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.pk, response.data['id'])

    def test_excluded_paths_dont_trigger_session_save(self):
        password = 'thisistestingpassword!'
        ca = fa.ClientAdministratorFactory(user__password=password)
        data = {'email': ca.user.email, 'password': password}

        url = reverse('user-login')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        expire_time = response.cookies['sessionid']['expires']

        # expire time on cookie is only accurate to seconds
        time.sleep(1)

        # excluded paths
        response2 = self.client.get(reverse('notification-list'))
        response3 = self.client.get(reverse('user-notifications-count'))
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response3.status_code, 200)

        # assert session wasn't updated with new time
        self.assertIsNone(response3.cookies.get('sessionid'))

        # non-excluded path
        response4 = self.client.get(reverse('job-list'))
        self.assertEqual(response4.status_code, 200)
        self.assertNotEqual(response4.cookies['sessionid']['expires'], expire_time)
