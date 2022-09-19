from unittest.mock import patch
from django.test import TestCase

from core.models import CandidateFile
import core.fixtures as f

from django.core.files.uploadedfile import SimpleUploadedFile


class TestCandidateFileSaved(TestCase):

    file_model = CandidateFile

    def setUp(self):
        self.client_org = f.create_client()

        self.candidate = f.create_candidate(self.client_org)
        self.file_record = self.create_file_record()
        self.file_record.save()

    def tearDown(self):
        self.file_record.file.delete()

    @staticmethod
    def create_file():
        return SimpleUploadedFile('irrelevant.txt', b'Complete gibberish')

    def create_file_record(self):
        instance = self.file_model()
        instance.organization = self.client_org
        instance.file = self.create_file()
        instance.candidate = self.candidate
        return instance

    @patch('core.signals.create_candidate_file_preview_and_thumbnail.delay')
    def test_create(self, task):
        instance = self.create_file_record()
        instance.save()

        task.assert_called_once_with(instance.id)

    @patch('core.signals.create_candidate_file_preview_and_thumbnail.delay')
    def test_update(self, task):
        instance = self.file_record
        instance.file = self.create_file()
        instance.save()

        task.assert_not_called()
