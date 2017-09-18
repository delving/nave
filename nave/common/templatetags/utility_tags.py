from django import template
from django.http import QueryDict

register = template.Library()

@register.filter
def replace_string(value, args):
    # usage in template: {{ data.item.field.url|replace_string:"find=&amp;=&replace=&" }}
    qs = QueryDict(args)
    if 'find' in qs and 'replace' in qs:
        return value.replace(qs['find'], qs['replace'])
    else:
        return value


@register.filter
def sort_alpha_lower(lst, key_name):
    return sorted(lst, key=lambda item: getattr(item, key_name).lower())