from unittest.mock import patch

from django.test import TestCase

from core import fixtures as f
from core import models as m
from core.user_activation import activate_user, get_agency_admin_activation_data


def create_unactivated_user(action=None, params=None):
    user = f.create_user('test@test.com')
    user.is_activated = False
    user.on_activation_action = action
    user.on_activation_params = params
    user.save()
    return user


class UserActivationTestCase(TestCase):
    def test_activate_user(self):
        user = create_unactivated_user()
        activate_user(user)
        self.assertEqual(user.is_activated, True)

    def test_activate_user_already_activated(self):
        user = create_unactivated_user()
        user.is_activated = True
        user.save()

        with self.assertRaises(ValueError):
            activate_user(user)

    def test_activate_user_action(self):
        called = False
        called_with_user = None
        called_with_params = None

        def activation_fn(user, **params):
            nonlocal called
            nonlocal called_with_user
            nonlocal called_with_params

            called = True
            called_with_user = user
            called_with_params = params

        activation_functions = {'activation_fn': activation_fn}
        expected_params = {'x': 1, 'y': 2}

        user = create_unactivated_user('activation_fn', expected_params)

        with patch(
            'core.user_activation.USER_ACTIVATION_FUNCTIONS', activation_functions
        ):

            activate_user(user)

        self.assertEqual(user.is_activated, True)
        self.assertTrue(called)
        self.assertEqual(called_with_user, user)
        self.assertEqual(called_with_params, expected_params)


class MakeUserAgencyAdminTestCase(TestCase):
    def test_get_agency_admin_activation_data(self):
        agency = f.create_agency()
        data = get_agency_admin_activation_data(agency)

        self.assertEqual(
            data,
            {
                'on_activation_action': 'make_user_agency_admin',
                'on_activation_params': {'agency_id': agency.id, 'job_id': None,},
            },
        )

    def test_get_agency_admin_activation_data_with_job(self):
        client = f.create_client()
        job = f.create_job(client)
        agency = f.create_agency()
        data = get_agency_admin_activation_data(agency, job)

        self.assertEqual(
            data,
            {
                'on_activation_action': 'make_user_agency_admin',
                'on_activation_params': {'agency_id': agency.id, 'job_id': job.id,},
            },
        )

    def test_make_user_agency_admin(self):
        agency = f.create_agency()
        data = get_agency_admin_activation_data(agency)

        user = create_unactivated_user(
            action=data['on_activation_action'], params=data['on_activation_params']
        )

        activate_user(user)

        self.assertTrue(m.Recruiter.objects.filter(user=user).exists())

    def test_make_user_agency_admin_with_job(self):
        client = f.create_client()
        job = f.create_job(client)
        agency = f.create_agency()
        data = get_agency_admin_activation_data(agency, job)

        user = create_unactivated_user(
            action=data['on_activation_action'], params=data['on_activation_params']
        )

        activate_user(user)

        self.assertTrue(m.Recruiter.objects.filter(user=user).exists())
        # TODO: Rework user activation for new contracting system
        self.assertTrue(
            m.Contract.objects.filter(agency=agency, client=client).exists()
        )
        self.assertTrue(job.agencies.filter(id=agency.id).exists())
