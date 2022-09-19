from django.test import TestCase


from core.factories import ClientFactory, ClientJobFactory, CareerSiteJobPostingFactory


class ClientChanged(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_org = ClientFactory(is_career_site_enabled=True,)

    @classmethod
    def generate_job_postings(cls, amount, is_enabled):
        for i in range(amount):
            job = ClientJobFactory(client=cls.client_org)
            yield CareerSiteJobPostingFactory(job=job, is_enabled=is_enabled)

    def test_career_site_disabled(self):
        job_postings = [
            *self.generate_job_postings(5, is_enabled=True),
            *self.generate_job_postings(5, is_enabled=False),
        ]
        self.client_org.is_career_site_enabled = False
        self.client_org.save()

        for i, posting in enumerate(job_postings):
            posting.refresh_from_db()
            self.assertFalse(posting.is_enabled, msg=f'job_posting[{i}] is enabled')

    def test_career_site_enabled(self):
        self.client_org.is_career_site_disabled = False
        self.client_org.save()
        disabled_job_postings = [*self.generate_job_postings(5, is_enabled=False)]
        self.client_org.is_career_site_disabled = True
        self.client_org.save()

        for i, posting in enumerate(disabled_job_postings):
            posting.refresh_from_db()
            self.assertFalse(
                posting.is_enabled, msg=f'disabled_job_posting[{i}] is enabled'
            )
