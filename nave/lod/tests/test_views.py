# -*- coding: utf-8 -*-
"""
Testing the various elements of the LoD views

"""
import pytest
from django.test import override_settings

from lod import tasks
from lod.utils import mimetype
from lod.views import *


def test_get_lod_mime_type(rf):
    request = rf.get("/resource/document/dataset/id")
    request.META['HTTP_ACCEPT'] = mimetype.TURTLE_MIME
    assert get_lod_mime_type('ttl', request) == mimetype.TURTLE_MIME
    assert get_lod_mime_type(None, request) == mimetype.TURTLE_MIME
    request.META['HTTP_ACCEPT'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    assert get_lod_mime_type(None, request) == ''


def test_http_response_see_other_redirect():
    assert HttpResponseSeeOtherRedirect.status_code == 303


@pytest.mark.django_db
@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')
def test_cache_page_redirect_if_not_found(rf):
    request = rf.get(
        '/nl/page/cache/http%3A//data.cultureelerfgoed.nl/semnet/7403e26d-cf33-4372-ad72-a2f9fcf8f63b',
        follow=True
    )
    store = rdfstore._rdfstore_test
    store._clear_all()
    assert CacheResource.objects.count() == 0
    view = LoDHTMLView.as_view(store=store)
    response = view(request)
    assert response.status_code == 302
    assert response.url.startswith('http://data.cultureelerfgoed.nl')
    assert CacheResource.objects.count() == 1
    task_response = tasks.retrieve_and_cache_remote_lod_resource.delay(response.url, store)
    assert task_response.result[0].result
    assert task_response.result[1] == False
    assert CacheResource.objects.count() == 1
    cache_resource = CacheResource.objects.first()
    assert cache_resource.stored
    assert cache_resource.source_rdf
    assert store.ask(uri=response.url)
    view = LoDHTMLView.as_view(store=store)
    response = view(request)
    assert response.status_code == 200
    assert response.template_name == ['rdf/lod_detail.html']


@pytest.mark.django_db
@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')
def test_cache_page_redirect_if_not_found(rf):
    request = rf.get(
        '/nl/page/cache/http%3A//sws.geonames.org/2755003/about.rdf',
        follow=True
    )
    store = rdfstore._rdfstore_test
    store._clear_all()
    assert CacheResource.objects.count() == 0
    view = LoDHTMLView.as_view(store=store)
    response = view(request)
    assert response.status_code == 302
    assert response.url.startswith("http://sws.geonames.org/2755003")


def test_lod_redirect_view(rf, settings):
    request = rf.get("/resource/document/id", follow=True)
    view = LoDRedirectView.as_view()
    response = view(request, type_="document", label="id")
    assert response.status_code == 303
    assert response.url.endswith("/page/document/id")
    request.META['HTTP_ACCEPT'] = "text/plain"
    # test edm
    settings.USE_EDM_BINDINGS = True
    response = view(request, type_="aggregation", label="id")
    assert response.status_code == 303
    assert response.url.endswith("/page/aggregation/id")

    response = view(request, type_="document", label="id")
    assert response.status_code == 303
    assert response.url.endswith("/page/document/id")
    request.META['HTTP_ACCEPT'] = mimetype.TURTLE_MIME
    response = view(request, type_="document", label="id")
    assert response.status_code == 303
    assert response.url.endswith("/data/document/id.turtle")


@pytest.mark.django_db
def test_lod_data_view(rf):
    with pytest.raises(Http404):
        request = rf.get("/data/aggregation/id.turtle", follow=True)
        request.META['HTTP_ACCEPT'] = mimetype.TURTLE_MIME
        view = LoDDataView.as_view()
        response = view(request, type_="document", label="id")



