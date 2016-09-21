# -*- coding: utf-8 -*- 
"""This module tests the OAI-PMH provider functionality


"""
from django.test import RequestFactory

from nave.void.oaipmh import OAIProvider

rf = RequestFactory()


def _request(param_dict):
    return rf.get('api/oai-pmh', param_dict)


def test_create_harvest_steps():
    """Test how the resumptionToken is parsed and turned into filters."""
    request = _request({'verb': "Identify"})
    provider = OAIProvider()
    provider.create_harvest_steps(request)

    assert not provider.params
    assert provider.oai_verb == 'Identify'


def test_harvest_steps_list_verb():
    request = _request({'verb': 'ListRecords', 'set': 'ton-smits-huis', 'metadataPrefix': 'abm',
                        'until': '2015-01-01', 'from': '2010-01-01'})
    provider = OAIProvider()
    provider.create_harvest_steps(request)
    assert provider.oai_verb == "ListRecords"
    assert 'verb' not in provider.params
    assert provider.metadataPrefix == 'abm'
    assert 'metadataPrefix' not in provider.params
    assert len(provider.filters) == 4
    assert sorted(list(provider.filters.keys())) == sorted(['dataset__oai_pmh', 'dataset__spec', 'modified__lt', 'modified__gt'])


def test_generate_filters_from_token():
    provider = OAIProvider()
    token = "prefix=edm::from=2014-02-11::to=2015-02-15::set=ton-smits-huis::cursor=100::list_size=4432"
    provider.create_filters_from_token(token)
    assert provider.metadataPrefix == "edm"
    assert provider.cursor == 100
    assert provider.list_size == 4432
    assert len(provider.filters) == 4

