# -*- coding: utf-8 -*-


import urllib.request, urllib.parse, urllib.error

from django import template

from ..helper import UrlHelper

register = template.Library()


@register.simple_tag
def base_url(url):
    # pass
    url = UrlHelper(url)
    try:
        return url.get_path()
    except:
        return ''


@register.simple_tag
def add_params(url, **kwargs):
    url = UrlHelper(url)
    try:
        url.update_query_data(**kwargs)
        return url.get_full_path()
    except Exception as e:
        return ''


@register.simple_tag
def del_params(url, *args, **kwargs):
    url = UrlHelper(url)
    try:
        url.del_params(*args, **kwargs)
        return url.get_full_path()
    except Exception as e:
        return ''


@register.simple_tag
def overload_params(url, **kwargs):
    url = UrlHelper(url)
    try:
        url.overload_params(**kwargs)
        return url.get_full_path()
    except Exception as e:
        return ''


@register.assignment_tag
def url_params(url, **kwargs):
    u = UrlHelper(url)
    u.update_query_data(**kwargs)
    return u.get_full_path()


@register.simple_tag
def toggle_params(url, **kwargs):
    u = UrlHelper(url)
    u.toggle_params(**kwargs)
    return u.get_full_path()


@register.filter(name='quote')
def quote_param(value, safe='/'):
    return urllib.parse.quote(value, safe)


@register.filter(name='quote_plus')
def quote_param_plus(value, safe='/'):
    return urllib.parse.quote_plus(value, safe)


@register.simple_tag
def form_hidden_field(request, field):
    html = ''
    if request.GET.get(field):
        html = '<input type="hidden" name="'+field+'" value="'+request.GET.get(field)+'" />'
    return html


@register.simple_tag
def form_hidden_fields(request, exclude=[]):
    html = ''
    params = request.GET
    generator = (param for param in params)
    if len(exclude):
        generator = (param for param in params if param not in exclude)
    for param in generator:
        fields = request.GET.getlist(param)
        for field in fields:
            # extract the facet string value from after the first occurrence of ":"
            # only relevant to qf but will return correct value for "q=term" as well
            text = field.split(':', 1)[-1]
            html = html + '<input type="hidden" name="'+param+'" value="'+field.strip()+'" data-text="'+text.strip()+'"/>'
    return html

