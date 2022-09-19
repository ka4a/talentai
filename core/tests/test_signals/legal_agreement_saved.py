from django.test import TestCase

from core.factories import ClientFactory, ClientAdministratorFactory
from core.models import LegalAgreement

from django.core.files.uploadedfile import SimpleUploadedFile


class TestLegalAgreementSaved(TestCase):
    def setUp(self):
        self.client_obj = ClientFactory()
        self.admin_user = ClientAdministratorFactory().user

    @staticmethod
    def create_file():
        return SimpleUploadedFile('irrelevant.txt', b'Complete gibberish')

    def test_signal_updates_user(self):
        self.assertTrue(self.admin_user.is_legal_agreed)
        agreement = LegalAgreement.objects.create(
            file=self.create_file(), document_type='tandc', version=1
        )
        self.admin_user.refresh_from_db()
        self.assertFalse(self.admin_user.is_legal_agreed)

    def test_signal_updates_user_draft_only_agreements(self):
        self.assertTrue(self.admin_user.is_legal_agreed)
        agreement = LegalAgreement.objects.create(
            file=self.create_file(), document_type='tandc', version=1
        )
        self.admin_user.refresh_from_db()
        self.assertFalse(self.admin_user.is_legal_agreed)
        agreement.is_draft = True
        agreement.save()
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_legal_agreed)

    def test_signal_updates_user_no_agreements(self):
        self.assertTrue(self.admin_user.is_legal_agreed)
        agreement = LegalAgreement.objects.create(
            file=self.create_file(), document_type='tandc', version=1
        )
        self.admin_user.refresh_from_db()
        self.assertFalse(self.admin_user.is_legal_agreed)
        agreement.delete()
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_legal_agreed)

    def test_signal_updates_user_new_agreements(self):
        self.assertTrue(self.admin_user.is_legal_agreed)
        LegalAgreement.objects.create(
            file=self.create_file(), document_type='tandc', version=1
        )
        self.admin_user.refresh_from_db()
        self.assertFalse(self.admin_user.is_legal_agreed)

        self.admin_user.is_legal_agreed = True
        self.admin_user.save()
        LegalAgreement.objects.create(
            file=self.create_file(), document_type='tandc', version=2
        )
        self.admin_user.refresh_from_db()
        self.assertFalse(self.admin_user.is_legal_agreed)
