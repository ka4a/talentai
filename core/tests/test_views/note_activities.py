from unittest.mock import patch, ANY
from django.utils import timezone

from dateutil.parser import isoparse
from faker import Faker
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from core import factories as fa

faker = Faker()


class NoteActivityTests(APITestCase):
    def setUp(self):
        self.proposal = fa.ClientProposalFactory()
        self.admin = self.proposal.job.owner
        self.job = self.proposal.job
        self.recruiter = fa.ClientInternalRecruiterFactory(
            client_id=self.job.organization.id
        ).user
        self.job.recruiters.add(self.recruiter, self.admin)
        self.candidate = self.proposal.candidate

        self.client.force_login(self.admin)

    def generate_notes(self):
        fa.NoteActivityFactory.create_batch(
            5, proposal=self.proposal, author=self.admin
        )
        fa.NoteActivityFactory.create_batch(
            5, candidate=self.candidate, author=self.admin
        )
        fa.NoteActivityFactory.create_batch(5, job=self.job, author=self.admin)

    def test_get_list(self):
        self.generate_notes()
        params = {'proposal': self.proposal.id}
        response = self.client.get(reverse('note_activities-list'), data=params)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['count'], 5)
        old_date = timezone.now()
        for result_data in response_data['results']:
            next_date = isoparse(result_data['createdAt'])
            self.assertGreaterEqual(old_date, next_date)
            old_date = next_date

    @patch('core.models.Notification.send')
    def test_post_proposal_note(self, send_mock):
        data = {
            'proposal': self.proposal.id,
            'author': self.admin.id,
            'content': faker.paragraph(),
        }
        response = self.client.post(
            reverse('note_activities-list'), data=data, format='json'
        )
        self.assertEqual(response.status_code, 201, msg=response.data)
        response_data = response.json()
        for field, value in data.items():
            self.assertEqual(value, response_data[field], msg=f'field {field}')

        args, kwargs = send_mock.call_args
        send_mock.assert_called_once_with(self.recruiter, *args[1:], **kwargs)

    @patch('core.models.Notification.send')
    def test_patch_proposal_note(self, send_mock):
        note = fa.NoteActivityFactory(proposal=self.proposal, author=self.admin)
        note_content = note.content
        note_created_at = note.created_at
        note_updated_at = note.updated_at
        data = {'proposal': self.proposal.id, 'content': faker.paragraph()}
        url = reverse('note_activities-detail', kwargs={'pk': note.id})
        response = self.client.patch(url, data=data, format='json')
        self.assertEqual(response.status_code, 200, msg=response.data)
        response_data = response.json()
        self.assertEqual(data['content'], response_data['content'])
        self.assertNotEqual(note_content, response_data['content'])
        self.assertEqual(note_created_at, isoparse(response_data['createdAt']))
        self.assertNotEqual(note_updated_at, isoparse(response_data['updatedAt']))
        send_mock.assert_not_called()
