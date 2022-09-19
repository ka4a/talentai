from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import datetime, utc

import core.fixtures as f
from core.check_candidate_duplication import check_candidate_duplication


BASE_CREATION_TIME = datetime(2019, 8, 1, tzinfo=utc)

# Original candidates
JANE_SMITH = {
    'first_name': 'Jane',
    'last_name': 'Smith',
    'email': 'janesmith@localhost',
    'secondary_email': 'janesmith2@localhost',
    'first_name_kanji': 'ジェーン',
    'last_name_kanji': 'スミス',
}

JACK_DAWSON = {
    'first_name': 'Jack',
    'last_name': 'Dawson',
    'email': 'jackdawson@localhost',
    'secondary_email': 'jackdawson2@localhost',
    'first_name_kanji': 'ジャック',
    'last_name_kanji': 'ドーソン',
}


ZOHO_CANDIDATE = {
    'first_name': 'Zoho',
    'last_name': 'Candidate',
    'email': 'zohocandidate@localhost',
    'secondary_email': 'zohocandidate2@localhost',
    'zoho_id': 10242048,
}

LINKEDIN_CANDIDATE = {
    'first_name': 'Linkedin',
    'last_name': 'Candidate',
    'email': 'linkedincandidate@localhost',
    'secondary_email': 'linkedincandidate2@localhost',
    'linkedin_url': 'https://www.linkedin.com/in/linkedincandidate',
}

SUBMITTED_CANDIDATE_1 = {
    'first_name': 'Submitted 1',
    'last_name': 'Candidate 1',
    'email': 'submittedcandidate1@localhost',
}

SUBMITTED_CANDIDATE_2 = {
    'first_name': 'Submitted 1',
    'last_name': 'Candidate 1',
    'email': 'submittedcandidate2@localhost',
}

POSSIBLY_SUBMITTED_BY_OTHER = {
    'first_name': 'Submitted',
    'last_name': 'By other 1',
    'email': 'submittedbyother1@localhost',
}

ABSOLUTELY_SUBMITTED_BY_OTHER = {
    'first_name': 'Submitted',
    'last_name': 'By other 2',
    'email': 'submittedbyother2@localhost',
}

ARCHIVED_CANDIDATE = {
    'first_name': 'Archived',
    'last_name': 'Candidate',
    'email': 'archivedcandidate@localhost',
    'secondary_email': 'archivedcandidate2@localhost',
    'archived': True,
}


class TestCandidateDuplicationCheck(TestCase):
    def setUp(self):
        self.client_obj = f.create_client()
        self.agency = f.create_agency()
        self.client_admin = f.create_client_administrator(self.client_obj)
        self.agency_admin = f.create_agency_administrator(self.agency)
        self.job = f.create_job(self.client_obj)

        # Create candidates
        self.jane_smith = f.create_candidate(self.client_obj, **JANE_SMITH)
        self.jack_dawson = f.create_candidate(self.client_obj, **JACK_DAWSON)
        self.zoho_candidate = f.create_candidate(self.client_obj, **ZOHO_CANDIDATE)
        self.linkedin_candidate = f.create_candidate(
            self.client_obj, **LINKEDIN_CANDIDATE
        )
        self.archived_candidate = f.create_candidate(
            self.client_obj, **ARCHIVED_CANDIDATE
        )
        self.submitted_candidate_1 = f.create_candidate(
            self.client_obj, **SUBMITTED_CANDIDATE_1
        )
        self.submitted_candidate_2 = f.create_candidate(
            self.client_obj, **SUBMITTED_CANDIDATE_2
        )
        self.possibly_submitted_by_other = f.create_candidate(
            self.agency, **POSSIBLY_SUBMITTED_BY_OTHER
        )
        self.absolutely_submitted_by_other = f.create_candidate(
            self.agency, **ABSOLUTELY_SUBMITTED_BY_OTHER
        )

        # create proposals

        self.proposal_1 = f.create_proposal(
            self.job, self.submitted_candidate_1, self.client_admin
        )
        self.proposal_2 = f.create_proposal(
            self.job, self.submitted_candidate_2, self.client_admin
        )
        # possibly submitted by other org
        self.proposal_3 = f.create_proposal(
            self.job, self.possibly_submitted_by_other, self.agency_admin
        )
        # absolutely submitted by other org
        self.proposal_3 = f.create_proposal(
            self.job, self.absolutely_submitted_by_other, self.agency_admin
        )
        self.proposal_1.created_at = BASE_CREATION_TIME + timedelta(days=1)
        self.proposal_1.save()
        self.proposal_2.created_at = BASE_CREATION_TIME + timedelta(days=2)
        self.proposal_2.save()

    def get_formatted_duplication_results(self, new_candidate):
        results = check_candidate_duplication(new_candidate, self.client_admin.profile)

        duplicates = map(
            lambda item: {
                'id': item.id,
                'is_absolute': item.is_absolute,
                'is_submitted': item.is_submitted,
            },
            results['queryset'],
        )
        to_restore = map(lambda item: item.id, results['to_restore'])

        submitted = results['last_submitted']
        submitted = submitted.date() if submitted else None

        return {
            'duplicates': list(duplicates),
            'last_submitted': submitted,
            'to_restore': list(to_restore),
            'submitted_by_others': results['submitted_by_others'],
        }

    def test_possible_duplication_name(self):
        """Should find a candidate with same name"""
        check_results = self.get_formatted_duplication_results(
            {
                'first_name': self.jane_smith.first_name,
                'last_name': self.jane_smith.last_name,
                'email': f.generate_email(),
            }
        )
        self.assertEqual(
            check_results,
            {
                'duplicates': [
                    {
                        'id': self.jane_smith.id,
                        'is_absolute': False,  # possible duplication
                        'is_submitted': False,
                    }
                ],
                'submitted_by_others': None,
                'last_submitted': None,
                'to_restore': [],
            },
        )

    def test_possible_duplication_name_ja(self):
        """Should find a candidate with same Japanese name"""
        check_results = self.get_formatted_duplication_results(
            {
                'first_name': '',
                'last_name': '',
                'first_name_kanji': self.jane_smith.first_name_kanji,
                'last_name_kanji': self.jane_smith.last_name_kanji,
                'email': f.generate_email(),
            }
        )
        self.assertEqual(
            check_results,
            {
                'duplicates': [
                    {
                        'id': self.jane_smith.id,
                        'is_absolute': False,  # possible duplication
                        'is_submitted': False,
                    }
                ],
                'submitted_by_others': None,
                'last_submitted': None,
                'to_restore': [],
            },
        )

    def test_absolute_duplication_email(self):
        """Should find a candidate with same email"""
        check_results = self.get_formatted_duplication_results(
            {'first_name': '', 'last_name': '', 'email': self.jane_smith.email,}
        )
        self.assertEqual(
            check_results,
            {
                'duplicates': [
                    {
                        'id': self.jane_smith.id,
                        'is_absolute': True,  # absolute duplication
                        'is_submitted': False,
                    }
                ],
                'submitted_by_others': None,
                'last_submitted': None,
                'to_restore': [],
            },
        )

    def test_absolute_duplication_secondary_email(self):
        check_results = self.get_formatted_duplication_results(
            {
                'first_name': '',
                'last_name': '',
                'email': f.generate_email(),
                'secondary_email': self.jane_smith.secondary_email,
            }
        )
        self.assertEqual(
            check_results,
            {
                'duplicates': [
                    {
                        'id': self.jane_smith.id,
                        'is_absolute': True,  # absolute duplication
                        'is_submitted': False,
                    }
                ],
                'submitted_by_others': None,
                'last_submitted': None,
                'to_restore': [],
            },
        )

    def assert_same_duplicates(self, expected_duplicates, duplicates):
        self.assertEqual(len(expected_duplicates), len(duplicates))

        expected_duplicates_by_id = {item['id']: item for item in expected_duplicates}

        for duplicate in duplicates:
            self.assertEqual(expected_duplicates_by_id[duplicate['id']], duplicate)

    def test_possible_and_absolute_duplication(self):
        check_results = self.get_formatted_duplication_results(
            {
                'first_name': self.jack_dawson.first_name,
                'last_name': self.jack_dawson.last_name,
                'email': f.generate_email(),
                'secondary_email': self.jane_smith.secondary_email,
            }
        )
        expected_duplicates = [
            {
                'id': self.jack_dawson.id,
                'is_absolute': False,  # possible duplication,
                'is_submitted': False,
            },
            {
                'id': self.jane_smith.id,
                'is_absolute': True,  # absolute duplication
                'is_submitted': False,
            },
        ]
        self.assert_same_duplicates(
            expected_duplicates, check_results.pop('duplicates')
        )

        self.assertEqual(
            check_results,
            {'submitted_by_others': None, 'last_submitted': None, 'to_restore': [],},
        )

    def test_zoho_duplication(self):
        check_results = self.get_formatted_duplication_results(
            {
                'first_name': '',
                'last_name': '',
                'email': f.generate_email(),
                'zoho_id': self.zoho_candidate.zoho_id,
            }
        )
        self.assertEqual(
            check_results,
            {
                'duplicates': [
                    {
                        'id': self.zoho_candidate.id,
                        'is_absolute': True,  # absolute duplication,
                        'is_submitted': False,
                    }
                ],
                'submitted_by_others': None,
                'last_submitted': None,
                'to_restore': [],
            },
        )

    def test_linkedin_duplication(self):
        check_results = self.get_formatted_duplication_results(
            {
                'first_name': '',
                'last_name': '',
                'email': f.generate_email(),
                'linkedin_url': self.linkedin_candidate.linkedin_url,
            }
        )
        self.assertEqual(
            check_results,
            {
                'duplicates': [
                    {
                        'id': self.linkedin_candidate.id,
                        'is_absolute': True,  # absolute duplication,
                        'is_submitted': False,
                    }
                ],
                'submitted_by_others': None,
                'last_submitted': None,
                'to_restore': [],
            },
        )

    def test_submitted(self):
        check_results = self.get_formatted_duplication_results(
            {
                'first_name': '',
                'last_name': '',
                'email': self.submitted_candidate_2.email,
                'job': self.job.id,
            }
        )
        self.assertEqual(
            check_results,
            {
                'duplicates': [
                    {
                        'id': self.submitted_candidate_2.id,
                        'is_absolute': True,  # absolute duplication
                        'is_submitted': True,
                    }
                ],
                'submitted_by_others': None,
                'last_submitted': self.proposal_2.created_at.date(),
                'to_restore': [],
            },
        )

    def test_possibly_submitted_by_other(self):
        check_results = self.get_formatted_duplication_results(
            {
                'first_name': self.possibly_submitted_by_other.first_name,
                'last_name': self.possibly_submitted_by_other.last_name,
                'email': f.generate_email(),
                'job': self.job.id,
            }
        )
        self.assertEqual(
            check_results,
            {
                'duplicates': [],
                'submitted_by_others': 'POSSIBLE',
                'last_submitted': None,
                'to_restore': [],
            },
        )

    def test_absolutely_submitted_by_other(self):
        check_results = self.get_formatted_duplication_results(
            {
                'first_name': '',
                'last_name': '',
                'email': self.absolutely_submitted_by_other.email,
                'job': self.job.id,
            }
        )
        self.assertEqual(
            check_results,
            {
                'duplicates': [],
                'submitted_by_others': 'ABSOLUTE',
                'last_submitted': None,
                'to_restore': [],
            },
        )

    def test_restoring(self):
        check_results = self.get_formatted_duplication_results(
            {'first_name': '', 'last_name': '', 'email': self.archived_candidate.email,}
        )
        self.assertEqual(
            check_results,
            {
                'duplicates': [],
                'submitted_by_others': None,
                'last_submitted': None,
                'to_restore': [self.archived_candidate.id],
            },
        )
