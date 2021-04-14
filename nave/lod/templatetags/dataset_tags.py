import logging
import subprocess

from collections import namedtuple
from urllib.parse import urlparse

from django import template
from django.conf import settings
from django.http import QueryDict

from nave.lod.utils.resolver import RDFRecord, get_cache_url

register = template.Library()

logger = logging.getLogger(__name__)

@register.assignment_tag
def define(val=None):
  return val


@register.filter
def to_https(value):
    return value.replace('http:', 'https:')


@register.filter(name='lookup')
def get_binding(value, arg):
    return value[arg]


@register.filter
def replace_string(value, args):
    qs = QueryDict(args)
    if 'find' in qs and 'replace' in qs:
        return value.replace(qs['find'], qs['replace'])
    else:
        return value

@register.assignment_tag(takes_context=True)
def get_sorted_resources_by_rdftype(context, rdf_type, predicate, local_bindings=None, reverse=False):
    if not local_bindings:
        local_bindings = context['resources']
    resources = local_bindings.get_resources_by_rdftype(rdf_type)
    if not resources:
        return resources
    return sorted(resources, key=lambda r: r.get_first(predicate).value, reverse=reverse)

@register.assignment_tag(takes_context=True)
def get_resources_by_rdftype(context, rdf_type, local_bindings=None):
    if not local_bindings:
        local_bindings = context['resources']
    return local_bindings.get_resources_by_rdftype(rdf_type)


@register.assignment_tag(takes_context=True)
def get_resource_fields(context, fieldname, local_bindings=None):
    if not local_bindings:
        local_bindings = context['resources']

    return local_bindings.get_list(fieldname)

@register.assignment_tag(takes_context=True)
def get_unsorted_resource_fields(context, fieldname, local_bindings=None):
    if not local_bindings:
        local_bindings = context['resources']
    fields = local_bindings.get_list(fieldname, False)
    if fieldname in ['edm_hasView']:
        nonEmptyFields = []
        for field in fields:
            if field.has_resource:
                webrsc = field.get_resource
                if webrsc.get_first("nave_thumbLarge") or webrsc.get_first("ebucore_hasMimeType"):
                    nonEmptyFields.append(field)

        return nonEmptyFields

    return fields

@register.simple_tag(takes_context=True)
def get_resolved_uri(context, uri):
    """Returns resolved uri, or Cached URI."""
    request = context['request']
    request_base = urlparse(request.build_absolute_uri()).netloc
    rdf_base = urlparse(uri).netloc
    if request_base in settings.RDF_ROUTED_ENTRY_POINTS and rdf_base in RDFRecord.get_rdf_base_url():
        resolved_uri = uri.replace(rdf_base, request_base)
    elif rdf_base not in request_base:
        resolved_uri = get_cache_url(uri)
    else:
        return uri
    return resolved_uri


@register.simple_tag(takes_context=True)
def field_exists(context, fieldname, local_bindings=None):
    """
    returns if a field property is part of the graph bindings
    :return: Boolean
    """
    # todo finish this implementation
    bindings = local_bindings if local_bindings else context['resources']
    values = bindings.get_list(fieldname)
    return True if values else False


@register.assignment_tag(takes_context=True)
def has_value(context, fieldname, local_bindings=None):
    """
    returns true if given field contains value
    :param context:
    :param fieldname:
    :return: Boolean
    """
    bindings = local_bindings if local_bindings else context['resources']
    values = bindings.get_list(fieldname)
    return True if values else False


@register.assignment_tag(takes_context=True)
def get_value(context, fieldname):
    """
    returns the value of a given fieldname
    :param context:
    :param fieldname:
    :return: value
    """
    bindings = context['resources']
    request = context['request']
    value = bindings.get_first(fieldname)
    return {'request': request, 'value': value}


# ######### result detail predicate and field value display ############################

@register.inclusion_tag('rdf/tags/_webresource.html', takes_context=True)
def detail_webresource(context, alt="", indicators=False, thumbnail_nav=False, webresources=""):
    """
    :param context: page context
    :param fieldname: DataSet.MetadataRecord field name
    :return: string
    """
    thumbnail_nav = thumbnail_nav
    indicators = indicators
    webresources = webresources
    bindings = context['resources']
    alt = bindings[alt].value if bindings[alt] else []

    return {
        'indicators': indicators,
        'thumbnail_nav': thumbnail_nav,
        'webresources': webresources,
        'alt': alt
    }


MockRDFObject = namedtuple('MockRDFObject', ["value"])

@register.inclusion_tag('rdf/tags/_search-detail-media-preview.html', takes_context=True)
def detail_media_preview(
        context, fieldname, alt="", fullscreen=False, indicators=False,
        thumbnail_nav=False, uri="", webresources="", local_bindings=None):
    """
    :param context: page context
    :param fieldname: DataSet.MetadataRecord field name
    :return: string
    """
    if not local_bindings:
        local_bindings = context['resources']
    values = local_bindings.get_list(fieldname)
    rights = local_bindings.get_list('edm_rights')
    if not values:
        values = [MockRDFObject(local_bindings.get_about_thumbnail)]
    alt = local_bindings[alt].value if local_bindings[alt] else []
    fullscreen = fullscreen
    thumbnail_nav = thumbnail_nav
    indicators = indicators
    rights = rights
    uri = uri
    webresources = webresources

    # values = ['http://www.dcn-images.nl/img/BDM/BDM_09809.jpg', 'http://www.dcn-images.nl/img/BDM/BDM_00807.jpg', 'http://www.dcn-images.nl/img/BDM/BDM_01999.jpg']
    # values = ['http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\001305.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_44r_1.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_205r_1.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_44r_2.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_223v_1.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_249v_1.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_35r_1.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\001313.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_66r_1.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\001303.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_249v-250r.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_200r_1.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_202v-203r.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_172r_1.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_223v-224r.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_76v-77r.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_285v_2.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\001302.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_82r_1.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\001307.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\001306.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_285v_3.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_203r_1.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_271v_2.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_249v_2.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_85r_1.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_148.jpg',
    #     'http://igem.adlibsoft.com/wwwopacx/wwwopac.ashx?command=getcontent&server=images&value=bergh\\0217_164v_1.jpg']

    return {
        'values': values,
        'alt': alt,
        'fullscreen': fullscreen,
        'indicators': indicators,
        'thumbnail_nav': thumbnail_nav,
        'rights': rights,
        'uri':uri,
        'webresources': webresources
    }


@register.inclusion_tag('rdf/tags/_rdf_properties.html', takes_context=True)
def render_properties(context, resources, obj=None, items=None, predicate=None, level=1):
    if not items:
        if not obj:
            logger.error('Illegal call to render properties without obj_id or items')
            raise ValueError('Illegal call to render properties without obj_id or items')
        items = resources.get_resource(uri_ref=obj.id, obj=obj).get_items(as_tuples=True)
        # TODO: add rdf type information here <19-11-20, Sjoerd Siebinga> #
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


@register.simple_tag(takes_context=True)
def get_external_uri(context, absolute_uri):
    return RDFRecord.get_external_rdf_url(absolute_uri, context['request'])


@register.inclusion_tag('rdf/tags/_banner-detail-field.html', takes_context=False)
def banner_field(field_name, item, class_name, html_tag):
    exists = False
    value = None
    if field_name in item.fields:
        value = item.fields.get(field_name)
        if value:
            if len(value) > 0:
                value = value[0].get("value")
            if value:
                exists = True
    return {
        "exists": exists,
        "value": value,
        "class_name": class_name,
        "html_tag": html_tag
    }

@register.inclusion_tag('rdf/tags/type_templates/_skos_concept.html', takes_context=True)
def render_skos_concept(context, local_bindings):
    if not local_bindings:
        local_bindings = context['resources']
    return {
        'resources': local_bindings,
        'local_bindings': local_bindings,
        'request': context['request']
    }

#  ######### result detail return field value only  for media item ######################
@register.inclusion_tag('rdf/tags/_search-detail-field.html', takes_context=True)
def detail_field(
        context,
        fieldname,
        rdf_type=None,
        group_by_source=False,
        source_badge='nave_sourceTag',
        allow_html=False,
        is_link=False,
        new_query=False,
        new_facet_query=False,
        label=None,
        badge=None,
        show_predicate=True,
        multiple=False,
        separator='',
        word_limit=0,
        add_link=False,
        is_inline_data=False,
        is_authenticated=False,
        surround=None,
        predicate_uri=None,
        local_bindings=None,
        rdf_object=None,
        facet_label=None,
        value_only=False):
    """
    show a detail field value
    @fieldname: the fieldname whose data to retrieve
    :return: field(s) and predicate
    """

    bindings = local_bindings if local_bindings else context['resources']
    request = context['request']
    fields = None
    predicate = None
    if not facet_label:
        facet_label = fieldname

    try:
        if rdf_type:
            fields = []
            types = bindings.get_resources_by_rdftype(rdf_type)
            source_badge = bindings.get_uri_from_search_label(source_badge)
            if types:
                for r in types:
                    for f in r.get_list(fieldname):
                        f.generate_source_tags(source_badge)
                        fields.append(f)

                if group_by_source:
                    grouped = {}
                    for field in fields:
                        field_key = field.value.__str__()
                        if field_key in grouped:
                            f = grouped.get(field_key).add_source_tag(field.get_source_tags)
                            continue

                        grouped[field_key] = field

                    fields = list(grouped.values())

        elif not predicate_uri and not rdf_object:
            if not multiple:
                field = bindings[fieldname]
                if field:
                    fields = [field]
            else:
                fields = bindings.get_list(fieldname)
        else:
            fields = rdf_object.get_resource_field_value(field_name_uri=predicate_uri)

        if fields:
            predicate = fields[0].predicate
    except Exception as err:
        logger.debug(err, fields, predicate_uri, fieldname, rdf_type)
        #  if settings.DEBUG:
            #  __import__('pdb').set_trace()
        fields = None
        predicate = None

    return {
        'fields': fields,
        'fieldname': fieldname,
        'allow_html': allow_html,
        'label': label,
        'is_link': is_link,
        'is_inline_data': is_inline_data,
        'new_query': new_query,
        'new_facet_query': new_facet_query,
        'facet_label': facet_label,
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
        'group_by_source': group_by_source,
        'source_badge': badge,
    }


@register.simple_tag
def git_ver():
    """
    Retrieve and return the latest git commit hash ID and tag as a dict.
    """

    git_dirs = [settings.DJANGO_ROOT, settings.PROJECT_ROOT]

    versions = {}

    for git_dir in git_dirs:
        try:
            # Date and hash ID
            head = subprocess.Popen(
                "git -C {dir} log -1 --pretty=format:\"%h on %cd\" --date=short".format(dir=git_dir),
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            version = head.stdout.readline().strip().decode('utf-8')

            # Latest tag
            head = subprocess.Popen(
                "git -C {dir} describe --tags $(git -C {dir} rev-list --tags --max-count=1)".format(dir=git_dir),
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            latest_tag = head.stdout.readline().strip().decode('utf-8')

            git_string = "{v}, {t}".format(v=version, t=latest_tag)
        except Exception as ex:
            git_string = u'unknown'
        versions[git_dir] = git_string
    return versions
