import os

from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView
from nave.common import views

from nave.search.views import LegacyAPIRedirectView

admin.autodiscover()
urlpatterns = [
    url(r'^', include('nave.void.urls')),
    url(r'^version/$', views.nave_version),
    url(r'^', include('nave.webresource.urls')),
    url(r'^crossdomain.xml$', TemplateView.as_view(template_name='crossdomain.xml')),
    url(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt')),
    url(r'^humans.xml$', TemplateView.as_view(template_name='humans.txt')),
    url(r'^watchman/', include('watchman.urls')),
    url(r'^rosetta/', include('rosetta.urls')),
]

if settings.USE_WAGTAIL_CMS:
    from wagtail.wagtailadmin import urls as wagtailadmin_urls
    urlpatterns += i18n_patterns(
        url(r'^cms/', include(wagtailadmin_urls)),
        prefix_default_language=False
    )

urlpatterns += i18n_patterns(
    url(r'^admin/', include(admin.site.urls)),  # NOQA
    url(r'^api-auth', include('rest_framework.urls', namespace='rest_framework')),
    url(r'narthex/', views.NarthexRedirectView.as_view()),
    url(r'^api/search/$', LegacyAPIRedirectView.as_view(), name='api_redirect'),
    url(r'^', include('nave.projects.{}.urls'.format(settings.SITE_NAME))),
    url(r'^', include('nave.search.urls')),
    url(r'^', include('nave.virtual_collection.urls')),
    url(r'^', include('nave.lod.urls')),
    url(r'^', include('nave.search_widget.urls')),
    # template and data from nave.void app
    url(r'^statistics/', TemplateView.as_view(template_name="statistics.html")),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    prefix_default_language=False
)



if settings.USE_WAGTAIL_CMS:
    from wagtail.wagtailcore import urls as wagtail_urls
    urlpatterns += i18n_patterns(
        url(r'^', include(wagtail_urls)),
        prefix_default_language=False
    )

    if os.path.exists(os.path.join(settings.DJANGO_ROOT, "projects", settings.SITE_NAME, "wagtail_urls.py")):
        urlpatterns += [
            url(r'^', include('nave.projects.{}.wagtail_urls'.format(settings.SITE_NAME)))
        ]


staticurls = [('^%s$' % f, 'redirect_to', {'url': settings.STATIC_URL + f}) for f in
              ('crossdomain.xml', 'robots.txt', 'humans.txt')]


# This is only needed when using runserver.
if settings.DEBUG:
    import django
    urlpatterns = [
        url(r'^media/(?P<path>.*)$', django.views.static.serve,  # NOQA
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    ] + staticfiles_urlpatterns() + urlpatterns  # NOQA
