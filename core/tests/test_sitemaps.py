from core.models import Client
from datetime import datetime

from django.test import TestCase

from core.factories import (
    CareerSiteJobPostingFactory,
    ClientFactory,
)
from talentai.sitemaps import CareerSiteSitemap, CareerSiteJobPostingSiteMap


class CareerSiteSiteMapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ClientFactory.create_batch(5, unique=True, career_site=True)

    def test_sitemap(self):
        ClientFactory.create_batch(3, unique=True)
        sitemap = CareerSiteSitemap()
        self.assertEqual(len(sitemap.items()), 5)
        for item in sitemap.items():
            self.assertTrue(item.is_career_site_enabled)
            self.assertEqual(type(sitemap.lastmod(item)), datetime)
            self.assertIn(item.career_site_slug, sitemap.location(item))


class CareerSiteJobPostingSiteMapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_obj = ClientFactory(career_site=True)
        CareerSiteJobPostingFactory.create_batch(5)
        cls.client2_obj = ClientFactory(unique=True)
        CareerSiteJobPostingFactory(is_enabled=True, job__client=cls.client2_obj)

    def test_sitemap(self):
        CareerSiteJobPostingFactory.create_batch(3, is_enabled=False)
        sitemap = CareerSiteJobPostingSiteMap()
        self.assertEqual(len(sitemap.items()), 5)
        for item in sitemap.items():
            self.assertTrue(item.is_enabled)
            self.assertEqual(type(sitemap.lastmod(item)), datetime)
            self.assertIn(item.slug, sitemap.location(item))
            self.assertTrue(item.job.client.is_career_site_enabled)
