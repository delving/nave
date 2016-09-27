import os

from django.conf import settings
from django.conf.urls import *  # NOQA
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView
from solid_i18n.urls import solid_i18n_patterns
from common import views

admin.autodiscover()
urlpatterns = patterns('',
                       url(r'^', include('void.urls')),
                       )

if settings.USE_WAGTAIL_CMS:
    from wagtail.wagtailadmin import urls as wagtailadmin_urls

    urlpatterns += solid_i18n_patterns('',
                                       url(r'^cms/', include(wagtailadmin_urls)),
                                       )

urlpatterns += solid_i18n_patterns('',
                            url(r'^admin/', include(admin.site.urls)),  # NOQA
                            url(r'^api-auth', include('rest_framework.urls', namespace='rest_framework')),
                            url(r'narthex/', views.NarthexRedirectView.as_view()),
                            url(r'^', include('projects.{}.urls'.format(settings.SITE_NAME))),
                            url(r'^', include('search.urls')),
                            url(r'^', include('virtual_collection.urls')),
                            url(r'^', include('webresource.urls')),
                            (r'^crossdomain.xml$', TemplateView.as_view(template_name='crossdomain.xml')),
                            (r'^robots.txt$', TemplateView.as_view(template_name='robots.txt')),
                            (r'^humans.xml$', TemplateView.as_view(template_name='humans.txt')),
                            url(r'^hm/', include('health_monitor.urls')),
                            url(r'^', include('lod.urls')),
                            url(r'^', include('webresource.urls')),
                            url(r'^', include('search_widget.urls')),
                            url(r'^version/$', views.nave_version),
                            # template and data from void app
                            url(r'^statistics/', TemplateView.as_view(template_name="statistics.html")),
                            url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
                            )


if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += solid_i18n_patterns('',
                                       url(r'^rosetta/', include('rosetta.urls')),
                                       )

if settings.USE_WAGTAIL_CMS:
    from wagtail.wagtailcore import urls as wagtail_urls

    urlpatterns += solid_i18n_patterns('',
                                       url(r'^', include(wagtail_urls)),
                                       )
    if os.path.exists(os.path.join(settings.DJANGO_ROOT, "projects", settings.SITE_NAME, "wagtail_urls.py")):
        urlpatterns += patterns('',
                                url(r'^', include('projects.{}.wagtail_urls'.format(settings.SITE_NAME))))


staticurls = [('^%s$' % f, 'redirect_to', {'url': settings.STATIC_URL + f}) for f in
              ('crossdomain.xml', 'robots.txt', 'humans.txt')]


# This is only needed when using runserver.
if settings.DEBUG:
    urlpatterns = patterns('',
                           url(r'^media/(?P<path>.*)$', 'django.views.static.serve',  # NOQA
                               {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    ) + staticfiles_urlpatterns() + urlpatterns  # NOQA
