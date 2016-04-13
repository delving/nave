import logging
from urllib.parse import urlparse

from django import template
from django.conf import settings

from lod import get_rdf_base_url
from lod.utils.lod import get_cache_url

register = template.Library()

logger = logging.getLogger(__name__)


@register.filter(name='lookup')
def get_binding(value, arg):
    return value[arg]

@register.simple_tag(takes_context=True)
def get_resolved_uri(context, uri):
    """Returns resolved uri, or Cached URI."""
    request = context['request']
    request_base = urlparse(request.build_absolute_uri()).netloc
    rdf_base = urlparse(uri).netloc
    if request_base in settings.RDF_ROUTED_ENTRY_POINTS and rdf_base in get_rdf_base_url():
        resolved_uri = uri.replace(rdf_base, request_base)
    elif rdf_base not in request_base:
        resolved_uri = get_cache_url(uri)
    else:
        return uri
    return resolved_uri


@register.simple_tag(takes_context=True)
def field_exists(context, fieldname):
    """
    returns if a field property is part of the graph bindings

    :return: Boolean
    """
    # todo finish this implementation
    bindings = context['resources']
    values = bindings.get_list(fieldname)
    return True if values else False


# ######### result detail predicate and field value display ############################

@register.inclusion_tag('rdf/_search-detail-media-preview.html', takes_context=True)
def detail_media_preview(context, fieldname, alt="", fullscreen=False, thumbnail_nav=False):
    """
    :param context: page context
    :param fieldname: DataSet.MetadataRecord field name
    :return: string
    """
    bindings = context['resources']
    values = bindings.get_list(fieldname)
    alt = bindings[alt].value if bindings[alt] else []



    fullscreen = fullscreen
    thumbnail_nav = thumbnail_nav
    # values = ['http://www.dcn-images.nl/img/BDM/BDM_09809.jpg', 'http://www.dcn-images.nl/img/BDM/BDM_00807.jpg', 'http://www.dcn-images.nl/img/BDM/BDM_01999.jpg']
    return {'values': values, 'alt': alt, 'fullscreen': fullscreen, 'thumbnail_nav': thumbnail_nav}


@register.inclusion_tag('rdf/_rdf_properties.html', takes_context=True)
def render_properties(context, resources, obj=None, items=None, predicate=None, level=1):
    if not items:
        if not obj:
            logger.error('Illegal call to render properties without obj_id or items')
            raise ValueError('Illegal call to render properties without obj_id or items')
        items = resources.get_resource(uri_ref=obj.id, obj=obj).get_items(as_tuples=True)
    level += 1
    not_follow_list = [
        "ore:isAggregatedBy"
    ]
    request = context['request']
    nr_levels = context['nr_levels']
    if predicate and predicate.qname in not_follow_list:
        return None
    return {
        "items": items,
        "resources": resources,
        "level": level,
        "request": request,
        "nr_levels": nr_levels

    }


########## result detail return field value only  for media item ######################

@register.inclusion_tag('rdf/_search-detail-field.html', takes_context=True)
def detail_field(
        context,
        fieldname,
        allow_html=False,
        is_link=False,
        new_query=False,
        new_facet_query=False,
        label=None,
        show_predicate=True,
        multiple=False,
        separator='',
        word_limit=0,
        add_link=False,
        is_authenticated=False,
        surround=None,
        predicate_uri=None,
        rdf_object=None,
        value_only=False):
    """
    show a detail field value
    @fieldname: the fieldname whose data to retrieve
    :return: field(s) and predicate
    """
    bindings = context['resources']
    request = context['request']

    try:
        if not predicate_uri and not rdf_object:
            if not multiple:
                fields = [bindings[fieldname]]
            else:
                fields = bindings.get_list(fieldname)
        else:
            fields = rdf_object.get_resource_field_value(field_name_uri=predicate_uri)
        predicate = fields[0].predicate
    except Exception as err:
        logger.debug(err)
        fields = None
        predicate = None

    return {
        'fields': fields,
        'fieldname': fieldname,
        'allow_html': allow_html,
        'label': label,
        'is_link': is_link,
        'new_query': new_query,
        'new_facet_query': new_facet_query,
        'predicate': predicate,
        'show_predicate': show_predicate,
        'word_limit': word_limit,
        'separator': separator,
        'add_link': add_link,
        'is_authenticated': is_authenticated,
        'surround': surround,
        'resources': bindings,
        'request': request,
        'nr_levels': 4,
        'value_only': value_only,
    }
