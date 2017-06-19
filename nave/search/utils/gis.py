import math

import geojson
from geojson import Feature, FeatureCollection, Point
from pyproj import transform, Proj
from . import geohash

BOUNDING_BOX_PARAM_KEYS = ['min_x', 'min_y', 'max_x', 'max_y']

# Proj4 projection strings.  Note: no commas between the concatenated strings!
RD = ("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 "
      "+k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel "
      "+towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 "
      "+units=m +no_defs")
GOOGLE = ('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 '
          '+lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m '
          '+nadgrids=@null +no_defs +over')
WGS84 = ('+proj=latlong +datum=WGS84')

# Rijksdriehoeks stelsel.
rd_projection = Proj(RD)
google_projection = Proj(GOOGLE)
wgs84_projection = Proj(WGS84)


def standard_percision(x):
    """Return a standard percision of 6. """
    return math.ceil(x*1000000)/1000000


def rd_to_wgs84(x, y, standard=True):
    """Return GOOGLE coordinates from RD coordinates.

    >>> rd_to_wgs84(85530,446100)
    (4.375585, 51.998928)

    """
    east, north = transform(rd_projection, wgs84_projection, x, y)
    lat_long = (standard_percision(east), standard_percision(north)) if standard else (east, north)
    return lat_long



def create_bbox_filter(val, key=None):

    def valid_bbox_filter():
        valid_keys = BOUNDING_BOX_PARAM_KEYS.sort()
        values_are_valid = all(isinstance(coor, float) for coor in list(val.values()))
        return isinstance(val, dict) and val.keys.sort() is valid_keys and values_are_valid

    if not valid_bbox_filter:
        return
    key = key if key is not None else "point"

    geo_filter = {
        "geo_bounding_box": {
            key: {
                "bottom_left": {
                    "lat": val.get('min_x'),
                    "lon": val.get('min_y')
                },
                "top_right": {
                    "lat": val.get('max_x'),
                    "lon": val.get('max_y')
                }
            }
        }
    }
    return geo_filter


def get_lat_long_bounding_box(boundingbox_params):
    bounding_box = {}
    if all('.' in coor for coor in list(boundingbox_params.values())):
        bounding_box = {key: float(value) for key, value in list(boundingbox_params.items())}
    elif all('.' not in coor for coor in list(boundingbox_params.values())):
        # converting rd to lat long
        min_y, min_x = gis.rd_to_wgs84(boundingbox_params.get('min_x'), boundingbox_params.get('min_y'))
        max_y, max_x = gis.rd_to_wgs84(boundingbox_params.get('max_x'), boundingbox_params.get('max_y'))
        bounding_box['min_x'] = min_x
        bounding_box['min_y'] = min_y
        bounding_box['max_x'] = max_x
        bounding_box['max_y'] = max_y
    return bounding_box


def get_bounding_box_params(params):
    bounding_box_params = {}
    for key in BOUNDING_BOX_PARAM_KEYS:
        if key in params:
            bounding_box_params[key] = params.get(key)
    return bounding_box_params


def get_feature_collection(facets):
    features = []
    if 'geo_clusters' in facets:
        clusters = facets['geo_clusters']
        for place in clusters.buckets:
            total = place.doc_count
            geo_hash = place.key
            lat, lon = geohash.decode(geo_hash)
            center_point = Point(coordinates=(float(lon), float(lat)))
            properties = {'count': total}
            # todo: get the doc_id for individual keys as extra queries. doc_id is no longer returned.
            feature_id = None  # place.get('doc_id')
            properties['hash_key'] = place.key
            # if extra_properties:
                # properties.update(extra_properties)
            features.append(Feature(geometry=center_point, id=feature_id, properties=properties))
    return FeatureCollection(features)


def get_geojson(feature_collection, as_string=True):
    return geojson.dumps(feature_collection) if as_string else feature_collection


def places_as_geojson(facets):
    features = get_feature_collection(facets)
    return get_geojson(features)



