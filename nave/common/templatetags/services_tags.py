# -*- coding: utf-8 -*-
from django import template
from django.conf import settings

register = template.Library()


@register.filter(name='addcss')
def addcss(field, css):
    """
    Make it possible to add class values to form fields rendered inside templates.
    {{field|addcss:"form-control"}}
    :param field:
    :param css:
    :return:
    """
    return field.as_widget(attrs={"class": css})


@register.inclusion_tag('tags/google_analytics.html')
def google_analytics():
    """
    Returns a string with configured google analytics id from project settings
    :return: ga_id string
    """
    try:
        ga_id = settings.SERVICES["google_analytics"]["ga_id"]
    except:
        ga_id = None

    return {'ga_id': ga_id}


@register.inclusion_tag('tags/social_media.html')
def social_media():
    """
    Returns urls configured inthe project settings file for various social media services
    :return: social_media object containing urls to services
    """
    try:
        services = settings.SERVICES["social_media"]
    except:
        services = None

    return {'social_media': services}

