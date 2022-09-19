from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, mixins
from rest_framework.generics import get_object_or_404

from core import models as m, serializers as s
from core.utils.common import fix_for_yasg


class PublicCareerSiteOrganizationViewSet(
    viewsets.GenericViewSet, mixins.RetrieveModelMixin
):
    queryset = m.Client.objects.filter(is_career_site_enabled=True)

    serializer_class = s.CareerSiteOrganizationSerializer
    lookup_url_kwarg = 'slug'
    lookup_value_regex = '[-a-zA-Z0-9_]+'
    lookup_field = 'career_site_slug'


class CareerSiteSlugMixin:
    def get_client(self):
        return get_object_or_404(
            m.Client.objects.all(),
            career_site_slug=self.kwargs.get('slug'),
            is_career_site_enabled=True,
        )


class PublicCareerSiteJobPostingsViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    CareerSiteSlugMixin,
):
    queryset = m.CareerSiteJobPosting.public_objects.all()

    serializer_class = s.CareerSiteJobPostingPublicSerializer
    lookup_url_kwarg = 'job_slug'
    lookup_value_regex = '[-a-zA-Z0-9_]+'
    search_fields = (
        'title',
        'work_location',
        'mission',
        'responsibilities',
        'requirements',
    )

    @fix_for_yasg
    def get_queryset(self):
        client = self.get_client()

        return m.CareerSiteJobPosting.public_objects.filter(
            job__org_id=client.id,
            job__org_content_type=ContentType.objects.get(
                app_label='core', model='client'
            ),
        )

    def get_object(self):
        """Allow slugs but only use the id part to get object"""
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        job_id = self.kwargs.get(self.lookup_url_kwarg, '').split('-')[-1]

        obj = get_object_or_404(queryset, job_id=job_id)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
