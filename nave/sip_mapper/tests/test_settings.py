"""
Test settings for how the app specific django settings is loaded and accessed.
"""
import os

from sip_mapper import settings


test_key = "ENABLE_NARTHEX"


def test__settings__find_default():
    enable_narthex = settings.ENABLE_NARTHEX
    assert enable_narthex is not None
    assert enable_narthex


def test__settings__env_setting(monkeypatch):
    assert test_key not in os.environ
    monkeypatch.setenv(test_key, "false")
    # assert test_key in os.environ
    # TODO: add proper env setting tests
    # enable_narthex = settings.ENABLE_NARTHEX
    # assert enable_narthex is not None
    # assert not enable_narthex


def test__settings__from_django(settings):
    settings.ENABLE_NARTHEX = False
    enable_narthex = settings.ENABLE_NARTHEX
    assert enable_narthex is not None
    assert not enable_narthex
