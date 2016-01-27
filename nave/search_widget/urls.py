from django.conf.urls import *
from django.views.generic import TemplateView


urlpatterns = patterns(
    '',
    url(r'^search-widget$', TemplateView.as_view(template_name="search-widget-brand.html")),
)