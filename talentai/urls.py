"""talentai URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.contrib.sitemaps import views as sitemaps_views
from django.views.generic.base import TemplateView
from django.http import HttpResponse
from django.urls import path, re_path
from django.views.generic import View
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .sitemaps import CareerSiteJobPostingSiteMap, CareerSiteSitemap


class DummyView(View):
    """For creating dummy urls, that exist in React app.
    Might be useful for getting links via `reverse`.
    """

    def get(self, request, *args, **kwargs):
        return HttpResponse('')


openapi_info = openapi.Info(title='ZooKeep API', default_version='v1',)

schema_view = get_schema_view(
    openapi_info,
    validators=['flex'],  # , 'ssv'],
    public=True,
    permission_classes=(permissions.AllowAny,),
)

admin.site.site_header = 'ZooKeep Admin'

sitemaps = {
    'career_site': CareerSiteSitemap,
    'career_site_job_postings': CareerSiteJobPostingSiteMap,
}

urlpatterns = [
    path(
        'admin/logout/',
        LogoutView.as_view(**{'template_name': 'admin/registration/logged_out.html',}),
        name='admin-logout',
    ),
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemaps_views.index, {'sitemaps': sitemaps}),
    path(
        'robots.txt',
        TemplateView.as_view(template_name='robots.txt', content_type='text/plain',),
    ),
    path(
        'sitemap-<section>.xml',
        sitemaps_views.sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
    re_path(r'^api/', include('core.urls')),
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(),
        name='schema-json',
    ),
    path('job/<job_id>', DummyView.as_view(), name='job'),
    path('job/<job_id>/activity', DummyView.as_view(), name='job_activity'),
    path(
        'job/<job_id>/proposal/<proposal_id>', DummyView.as_view(), name='proposal_page'
    ),
    path(
        'job/<job_id>/proposal/<proposal_id>/activity',
        DummyView.as_view(),
        name='proposal_activity',
    ),
    path('a/approvals/fees/<fee_id>', DummyView.as_view(), name='fee_page',),
    path('candidate/<candidate_id>', DummyView.as_view(), name='candidate_page'),
    path(
        'candidate/<candidate_id>/activity',
        DummyView.as_view(),
        name='candidate_activity',
    ),
    path('career/<slug>', DummyView.as_view(), name='career_site_page'),
    path('career/<slug>/<job_slug>', DummyView.as_view(), name='career_site_job_page'),
    # Auth:
    path('login/', DummyView.as_view(), name='login'),
    path('logout/', DummyView.as_view(), name='logout'),
    path('forgot-password/', DummyView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', DummyView.as_view(), name='password_reset_confirm'),
    path('a/sign-up/invite/<token>', DummyView.as_view(), name='agency_sign_up_token'),
    path('account/activate/<token>', DummyView.as_view(), name='account_activate'),
    path('invitations/', DummyView.as_view(), name='invitations_page'),
    path(
        'confirm-interview/<uuid>/',
        DummyView.as_view(),
        name='select_interview_timeslot',
    ),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(
            r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')
        ),
        re_path(
            r'^swagger/$',
            schema_view.with_ui('swagger', cache_timeout=0),
            name='schema-swagger-ui',
        ),
    ]

    if settings.MEDIA_URL and settings.MEDIA_ROOT:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
