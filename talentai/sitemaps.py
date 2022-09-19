from django.contrib.sitemaps import Sitemap
from core.models import Client, CareerSiteJobPosting
from django.urls import reverse


class CareerSiteSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9
    protocol = 'https'

    def items(self):
        return Client.objects.filter(is_career_site_enabled=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('career_site_page', kwargs={'slug': obj.career_site_slug})


class CareerSiteJobPostingSiteMap(Sitemap):
    changefreq = 'daily'
    priority = 0.8
    protocol = 'https'

    def items(self):
        return CareerSiteJobPosting.public_objects.filter(
            job__client__is_career_site_enabled=True
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_public_url()
