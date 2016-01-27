import os

from django.conf import settings
from django.conf.urls import *  # NOQA
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView


admin.autodiscover()
urlpatterns = patterns('',
                       url(r'^', include('void.urls')),
                       )

urlpatterns += i18n_patterns('',
                            url(r'^admin/', include(admin.site.urls)),  # NOQA
                            url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
                            # todo: create new sitemap not based on DJANGO CMS
                            # url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': {'cmspages': CMSSitemap}}),
                            url(r'^', include('projects.{}.urls'.format(settings.SITE_NAME))),
                            url(r'^', include('search.urls')),
                            (r'^crossdomain.xml$', TemplateView.as_view(template_name='crossdomain.xml')),
                            (r'^robots.txt$', TemplateView.as_view(template_name='robots.txt')),
                            (r'^humans.xml$', TemplateView.as_view(template_name='humans.txt')),
                            url(r'^hm/', include('health_monitor.urls')),
                            url(r'^', include('lod.urls')),
                            url(r'^navigator/?$', TemplateView.as_view(template_name="navigator.html")),#mocked
                            url(r'^', include('search_widget.urls')),
                            url(r'^statistics/', TemplateView.as_view(template_name="statistics.html")), # template and data from void app
                            url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
                            )

staticurls = [('^%s$' % f, 'redirect_to', {'url': settings.STATIC_URL + f}) for f in
              ('crossdomain.xml', 'robots.txt', 'humans.txt')]

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
                            url(r'^rosetta/', include('rosetta.urls')),
                            )

# This is only needed when using runserver.
if settings.DEBUG:
    urlpatterns = patterns('',
                           url(r'^media/(?P<path>.*)$', 'django.views.static.serve',  # NOQA
                               {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    ) + staticfiles_urlpatterns() + urlpatterns  # NOQA