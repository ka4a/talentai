from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.serializers import PrimaryKeyRelatedField
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from core.utils import poly_relation_filter


from core import fixtures as f, models as m

OK = (200, None)
CREATED = (201, None)
DELETED = (204, None)
NOT_FOUND = (404, f.NOT_FOUND)
NO_PERMISSION = (403, f.NO_PERMISSION)
NOT_AUTHENTICATED = (403, f.NOT_AUTHENTICATED)


def no_candidate(candidate):
    return (
        400,
        {
            'candidate': [
                PrimaryKeyRelatedField.default_error_messages['does_not_exist'].format(
                    pk_value=candidate.id,
                )
            ]
        },
    )


class NotExistentFile:
    def delete(self):
        pass


class NotExistentFileRecord:
    def __init__(self, pk=-1):
        self.pk = pk
        self.id = pk
        self.file = NotExistentFile()
        self.preview = NotExistentFile()


class TestCandidateMiscFilesViewset(APITestCase):
    def setUp(self):
        self.users, self.org = f.get_org_users_map(
            {'client': 'client', 'agency': 'agency', 'contracted_agency': 'agency',}
        )

        f.create_contract(self.org['contracted_agency'], self.org['client'])

        self.job = f.create_job(self.org['client'])

        self.file_record_list = []

    def create_record(
        self,
        org_type=None,
        user_type=None,
        stage='longlist',
        is_shared=True,
        job_managed_by=None,
        proposal_count=1,
    ):
        candidate = f.create_candidate(self.org[org_type])

        for i in range(proposal_count):
            job = f.create_job(self.org['client'])
            if job_managed_by:
                job.assign_manager(self.users['client'][job_managed_by])

            f.create_proposal(
                job=job,
                candidate=candidate,
                created_by=self.users[org_type][user_type],
                stage=stage,
            )

        return m.CandidateFile.objects.create(
            candidate=candidate,
            organization=self.org[org_type],
            is_shared=is_shared,
            file=SimpleUploadedFile(f'irrelevant.txt', b'Gibberish'),
            preview=SimpleUploadedFile(f'irrelevant.pdf', b'Gibberish'),
        )

    def case_iterator(self, checks, cases):
        for org_type in checks:
            for user_type in checks[org_type]:
                for case in checks[org_type][user_type]:
                    user = self.users.get(org_type, dict()).get(user_type, None)

                    if user:
                        self.client.force_login(user)

                    msg = f'Case: "{case}", User: "{user_type}"'

                    yield {
                        'case': cases[case],
                        'assertion': checks[org_type][user_type][case],
                        'msg': msg,
                        'user': user,
                        'org': self.org.get(org_type),
                    }

                    self.client.logout()

    def assert_expected_response(self, expectation, response, msg):
        code, response_data = expectation

        self.assertEqual(code, response.status_code, msg)

        if response_data is not None:
            self.assertEqual(response_data, response.json(), msg)

    def check_access(self, url_name):
        checks = {
            'none': {
                'none': {
                    'client': NOT_AUTHENTICATED,
                    'agency': NOT_AUTHENTICATED,
                    'not_exist': NOT_AUTHENTICATED,
                }
            },
            'client': {
                'talent_associate': {
                    'client': OK,
                    'client_multiple_proposals': OK,
                    'agency': NOT_FOUND,
                    'agency_private': NOT_FOUND,
                    'contracted_longlist': NOT_FOUND,
                    'contracted_shortlist': OK,
                    'contracted_private': NOT_FOUND,
                    'not_exist': NOT_FOUND,
                },
                'hiring_manager': {
                    'client': OK,
                    'client_managed': OK,
                    'agency': NOT_FOUND,
                    'agency_managed': NOT_FOUND,
                    'agency_private': NOT_FOUND,
                    'contracted_longlist': NOT_FOUND,
                    'contracted_shortlist': NOT_FOUND,
                    'contracted_shortlist_managed': OK,
                    'contracted_private': NOT_FOUND,
                },
            },
            'agency': {
                'agency_administrator': {
                    'client': NOT_FOUND,
                    'agency': OK,
                    'agency_multiple_proposals': OK,
                    'agency_private': OK,
                    'agency_recruited': OK,
                    'contracted_longlist': NOT_FOUND,
                    'contracted_shortlist': NOT_FOUND,
                    'contracted_private': NOT_FOUND,
                    'not_exist': NOT_FOUND,
                },
                'agency_manager': {
                    'client': NOT_FOUND,
                    'agency': OK,
                    'agency_private': OK,
                    'agency_recruited': OK,
                    'contracted_longlist': NOT_FOUND,
                    'contracted_shortlist': NOT_FOUND,
                    'contracted_private': NOT_FOUND,
                },
                'recruiter': {
                    'client': NOT_FOUND,
                    'agency': OK,
                    'agency_private': OK,
                    'agency_recruited': OK,
                    'contracted_longlist': NOT_FOUND,
                    'contracted_shortlist': NOT_FOUND,
                    'contracted_private': NOT_FOUND,
                },
            },
        }

        file_records = {
            'not_exist': NotExistentFileRecord(),
            'client': self.create_record('client', 'talent_associate'),
            'client_multiple_proposals': self.create_record(
                'client', 'talent_associate', proposal_count=2
            ),
            'client_managed': self.create_record(
                'client', 'talent_associate', job_managed_by='hiring_manager'
            ),
            'agency': self.create_record('agency', 'agency_administrator'),
            'agency_multiple_proposals': self.create_record(
                'agency', 'agency_administrator', proposal_count=2
            ),
            'agency_managed': self.create_record(
                'agency', 'agency_administrator', job_managed_by='hiring_manager'
            ),
            'agency_private': self.create_record(
                'agency', 'agency_administrator', is_shared=False
            ),
            'agency_recruited': self.create_record('agency', 'recruiter',),
            'contracted_longlist': self.create_record(
                'contracted_agency', 'agency_administrator'
            ),
            'contracted_shortlist': self.create_record(
                'contracted_agency', 'agency_administrator', 'shortlist'
            ),
            'contracted_shortlist_managed': self.create_record(
                'contracted_agency',
                'agency_administrator',
                'shortlist',
                job_managed_by='hiring_manager',
            ),
            'contracted_private': self.create_record(
                'contracted_agency', 'agency_administrator'
            ),
        }

        try:
            for props in self.case_iterator(checks, file_records):
                self.assert_expected_response(
                    expectation=props['assertion'],
                    response=self.client.get(
                        reverse(url_name, kwargs={'pk': props['case'].id})
                    ),
                    msg=props['msg'],
                )
        finally:
            for record in file_records.values():
                record.file.delete()
                record.preview.delete()

    def test_retrieve(self):
        self.check_access('candidate-misc-file-detail')

    def test_preview(self):
        self.check_access('candidate-misc-file-preview')

    def test_create(self):
        candidates = {key: f.create_candidate(value) for key, value in self.org.items()}

        no_client_candidate = no_candidate(candidates['client'])
        no_agency_candidate = no_candidate(candidates['agency'])
        no_contracted_candidate = no_candidate(candidates['contracted_agency'])

        checks = {
            'none': {
                'none': {'client': NOT_AUTHENTICATED, 'agency': NOT_AUTHENTICATED,}
            },
            'client': {
                'talent_associate': {
                    'client': CREATED,
                    'agency': no_agency_candidate,
                    'contracted_agency': no_contracted_candidate,
                },
                'hiring_manager': {
                    'client': CREATED,
                    'agency': no_agency_candidate,
                    'contracted_agency': no_contracted_candidate,
                },
            },
            'agency': {
                'agency_administrator': {
                    'client': no_client_candidate,
                    'agency': CREATED,
                    'contracted_agency': no_contracted_candidate,
                },
                'agency_manager': {
                    'client': no_client_candidate,
                    'agency': CREATED,
                    'contracted_agency': no_contracted_candidate,
                },
                'recruiter': {
                    'client': no_client_candidate,
                    'agency': CREATED,
                    'contracted_agency': no_contracted_candidate,
                },
            },
        }

        created_before = []
        for props in self.case_iterator(checks, candidates):

            try:
                file_name = 'irrelevant.txt'
                response = self.client.post(
                    reverse('candidate-misc-file-list'),
                    {
                        'file': SimpleUploadedFile(file_name, b'Gibberish'),
                        'is_shared': True,
                        'candidate': props['case'].id,
                    },
                )

                self.assert_expected_response(
                    props['assertion'], response, props['msg']
                )

                if response.status_code == CREATED[0]:
                    created_qs = m.CandidateFile.objects.filter(
                        poly_relation_filter(
                            'org_id', 'org_content_type', props['org']
                        ),
                        candidate=props['case'],
                        is_shared=True,
                    ).exclude(id__in=created_before)
                    self.assertEqual(len(created_qs), 1, props['msg'])

                    instance = created_qs[0]

                    self.assertTrue(
                        instance.file.name.endswith(file_name), props['msg']
                    )

                    created_before.append(instance.id)

            except Exception as e:
                print(props['msg'])
                raise e

    def test_update(self):
        checks = {
            'none': {
                'none': {'client': NOT_AUTHENTICATED, 'agency': NOT_AUTHENTICATED,}
            },
            'client': {
                'talent_associate': {
                    'client': OK,
                    'agency': NOT_FOUND,
                    'agency_shared': NOT_FOUND,
                    'contracted_agency': NOT_FOUND,
                    'contracted_agency_shared': NOT_FOUND,
                },
                'hiring_manager': {
                    'client': OK,
                    'agency': NOT_FOUND,
                    'contracted_agency': NOT_FOUND,
                },
            },
            'agency': {
                'agency_administrator': {
                    'client': NOT_FOUND,
                    'client_shared': NOT_FOUND,
                    'agency': OK,
                    'contracted_agency': NOT_FOUND,
                },
                'agency_manager': {
                    'client': NOT_FOUND,
                    'agency': OK,
                    'contracted_agency': NOT_FOUND,
                },
                'recruiter': {
                    'client': NOT_FOUND,
                    'agency': OK,
                    'contracted_agency': NOT_FOUND,
                },
            },
        }

        cases = {
            'client': (
                {'is_shared': True},
                self.create_record('client', 'talent_associate', is_shared=False),
            ),
            'agency': (
                {'is_shared': True},
                self.create_record('agency', 'agency_administrator', is_shared=False),
            ),
            'client_shared': (
                {'is_shared': False},
                self.create_record('client', 'talent_associate'),
            ),
            'agency_shared': (
                {'is_shared': False},
                self.create_record('agency', 'agency_administrator'),
            ),
            'contracted_agency': (
                {'is_shared': True},
                self.create_record(
                    'contracted_agency', 'agency_administrator', is_shared=False
                ),
            ),
            'contracted_agency_shared': (
                {'is_shared': True},
                self.create_record('contracted_agency', 'agency_administrator'),
            ),
        }

        try:
            for props in self.case_iterator(checks, cases):
                data, instance = props['case']

                response = self.client.patch(
                    reverse('candidate-misc-file-detail', kwargs={'pk': instance.id}),
                    data,
                )

                self.assert_expected_response(
                    props['assertion'], response, props['msg']
                )

                if response.status_code == OK[0]:
                    self.assertEqual(
                        len(m.CandidateFile.objects.filter(id=instance.id, **data)),
                        1,
                        props['msg'],
                    )
        finally:
            for _, record in cases.values():
                record.file.delete()
                record.preview.delete()

    def test_delete(self):
        checks = {
            'none': {
                'none': {'client': NOT_AUTHENTICATED, 'agency': NOT_AUTHENTICATED,}
            },
            'client': {
                'talent_associate': {
                    'client': DELETED,
                    'agency': NOT_FOUND,
                    'agency_shared': NOT_FOUND,
                    'contracted_agency': NOT_FOUND,
                    'contracted_agency_shared': NOT_FOUND,
                },
                'hiring_manager': {
                    'client': DELETED,
                    'agency': NOT_FOUND,
                    'contracted_agency': NOT_FOUND,
                },
            },
            'agency': {
                'agency_administrator': {
                    'client': NOT_FOUND,
                    'client_shared': NOT_FOUND,
                    'agency': DELETED,
                    'contracted_agency': NOT_FOUND,
                },
                'agency_manager': {
                    'client': NOT_FOUND,
                    'agency': DELETED,
                    'contracted_agency': NOT_FOUND,
                },
                'recruiter': {
                    'client': NOT_FOUND,
                    'agency': DELETED,
                    'contracted_agency': NOT_FOUND,
                },
            },
        }

        cases = {
            'client': self.create_record('client', 'talent_associate', is_shared=False),
            'agency': self.create_record(
                'agency', 'agency_administrator', is_shared=False
            ),
            'client_shared': self.create_record('client', 'talent_associate'),
            'agency_shared': self.create_record('agency', 'agency_administrator'),
            'contracted_agency': self.create_record(
                'contracted_agency', 'agency_administrator', is_shared=False
            ),
            'contracted_agency_shared': self.create_record(
                'contracted_agency', 'agency_administrator'
            ),
        }
        try:
            for props in self.case_iterator(checks, cases):
                instance = props['case']

                response = self.client.delete(
                    reverse('candidate-misc-file-detail', kwargs={'pk': instance.id}),
                )

                self.assert_expected_response(
                    props['assertion'], response, props['msg']
                )

                if response.status_code == DELETED[0]:
                    self.assertFalse(
                        m.CandidateFile.objects.filter(id=instance.id).exists(),
                        props['msg'],
                    )

                instance.save()
        finally:
            for record in cases.values():
                record.file.delete()
                record.preview.delete()
