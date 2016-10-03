# -*- coding: utf-8 -*-
"""Pytest fixtures.

This module contains pytest fixtures available to all unit-tests.
"""

import pytest


@pytest.fixture(scope='function')
def boyscout(request):
    """Fixture to test for docstrings in modules and functions."""
    assert request.function.__doc__
    assert request.module.__doc__
