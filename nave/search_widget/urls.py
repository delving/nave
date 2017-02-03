from django.conf.urls import *
from django.views.generic import TemplateView


urlpatterns = [
    url(r'^search-widget$', TemplateView.as_view(template_name="search-widget-brand.html")),
]
