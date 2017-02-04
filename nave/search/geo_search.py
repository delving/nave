"""The GeoSearch extensions."""
from elasticsearch_dsl import Search


class GeoSearch(Search):
    """ES Search class with additional GIS query support."""
    pass

# class GeoS(S):
#     BOUNDING_BOX_PARAM_KEYS = ['min_x', 'min_y', 'max_x', 'max_y']
#
#     def process_filter_bbox(self, key, val, action):
#
#         def valid_bbox_filter():
#             valid_keys = self.BOUNDING_BOX_PARAM_KEYS.sort()
#             values_are_valid = all(isinstance(coor, float) for coor in list(val.values()))
#             return isinstance(val, dict) and val.keys.sort() is valid_keys and values_are_valid
#
#         if not valid_bbox_filter:
#             return
#         key = key if key is not None else "point"
#
#         geo_filter = {
#             "geo_bounding_box": {
#                 key: {
#                     "bottom_left": {
#                         "lat": val.get('min_x'),
#                         "lon": val.get('min_y')
#                     },
#                     "top_right": {
#                         "lat": val.get('max_x'),
#                         "lon": val.get('max_y')
#                     }
#                 }
#             }
#         }
#         return geo_filter
#
#     def process_filter_polygon(self, key, val, action):
#         # TODO finish implementation
#         """
#         Filter results by polygon
#         http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl-geo-polygon-filter.html
#         """
#
#         def valid_polygon_filter():
#             valid_keys = self.BOUNDING_BOX_PARAM_KEYS.sort()
#             values_are_valid = all(isinstance(coor, float) for coor in list(val.values()))
#             return isinstance(val, dict) and val.keys.sort() is valid_keys and values_are_valid
#
#         if not valid_polygon_filter:
#             return
#         key = key if key is not None else "point"
#
#         polygon_filter = {
#             "geo_polygon": {
#                 key: [
#                         {"lat": 40, "lon": -70},
#                         {"lat": 30, "lon": -80},
#                         {"lat": 20, "lon": -90}
#                     ]
#             }
#         }
#         return polygon_filter
#
#     def facet_geocluster(self, filtered=True, factor=0.6):
#         """Add facets for clustered geo search.
#
#         Note: It should always be the last in the chain
#         """
#         cluster_config = {
#             "geohash": {
#                 "field": "point",
#                 "factor": factor,
#                 'show_doc_id': True
#             }
#         }
#         query = self.query()
#         if filtered:
#             filt = query.build_search().get('filter')
#             filtered = {'facet_filter': filt}
#             filtered.update(cluster_config)
#             cluster_config = filtered
#         return query.facet_raw(places=cluster_config)
#
#     @staticmethod
#     def get_feature_collection(facets):
#         features = []
#         if 'places' in facets:
#             for place in facets.get('places').clusters:
#                 total = place.get('total', 0)
#                 center = place.get('center')
#                 center_point = Point((center['lon'], center['lat']))
#                 properties = {'count': total}
#                 feature_id = place.get('doc_id')
#                 extra_properties = {key: place.get(key) for key in list(place.keys()) if key in ['doc_type']}
#                 if extra_properties:
#                     properties.update(extra_properties)
#                 features.append(Feature(geometry=center_point, id=feature_id, properties=properties))
#         return FeatureCollection(features)
#
#     @staticmethod
#     def get_geojson(feature_collection):
#         return geojson.dumps(feature_collection)
#
#     def places_as_geojson(self, facets):
#         features = self.get_feature_collection(facets)
#         return self.get_geojson(features)
#
#     @staticmethod
#     def get_lat_long_bounding_box(boundingbox_params):
#         bounding_box = {}
#         if all('.' in coor for coor in list(boundingbox_params.values())):
#             bounding_box = {key: float(value) for key, value in list(boundingbox_params.items())}
#         elif all('.' not in coor for coor in list(boundingbox_params.values())):
#             # converting rd to lat long
#             min_y, min_x = gis.rd_to_wgs84(boundingbox_params.get('min_x'), boundingbox_params.get('min_y'))
#             max_y, max_x = gis.rd_to_wgs84(boundingbox_params.get('max_x'), boundingbox_params.get('max_y'))
#             bounding_box['min_x'] = min_x
#             bounding_box['min_y'] = min_y
#             bounding_box['max_x'] = max_x
#             bounding_box['max_y'] = max_y
#         return bounding_box
