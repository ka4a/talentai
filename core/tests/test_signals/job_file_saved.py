from unittest.mock import patch
from django.test import TestCase

from core.models import JobFile
import core.fixtures as f

from django.core.files.uploadedfile import SimpleUploadedFile


class TestJobFileSaved(TestCase):

    file_model = JobFile

    def setUp(self):
        client = f.create_client()

        self.job = f.create_job(client)
        self.file_record = self.create_file_record()
        self.file_record.save()

    def tearDown(self):
        self.file_record.file.delete()

    @staticmethod
    def create_file():
        return SimpleUploadedFile('irrelevant.txt', b'Complete gibberish')

    def create_file_record(self):
        instance = self.file_model()
        instance.file = self.create_file()
        instance.job = self.job
        return instance

    @patch('core.signals.convert_job_file.delay')
    def test_create(self, task):
        instance = self.create_file_record()
        instance.save()

        task.assert_called_once_with(instance.id)

    @patch('core.signals.convert_job_file.delay')
    def test_update(self, task):
        instance = self.file_record
        instance.file = self.create_file()
        instance.save()

        task.assert_not_called()
