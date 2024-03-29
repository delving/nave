"""
Note:

    Make sure this url configuration is included in your main configuration
    as follows:

    url(r'^', include('webresource.urls')),
"""
from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'api/webresource/$',
        views.WebResourceRedirectView.as_view(),
        name="webresource"
    ),
    url(
        r'api/webresource/deepzoom/(?P<urn>.*$)',
        views.DeepZoomRedirectView.as_view(),
        name="webresource_deepzoom"
    ),
    url(
        r'api/deepzoom/(?P<webresource>.*$)',
        views.DeepZoomRedirectView.as_view(),
        name="webresource_deepzoom_resolve"
    ),
    url(
        r'api/webresource/_docs/$',
        views.webresource_docs,
        name="webresource_docs"
    )
    # todo: include the references to statistics as well
    # for example _statistics _docs etc
]
