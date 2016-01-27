# -*- coding: utf-8 -*- 
from search.search import NaveESQuery, UserQuery


def test__createbreadcrumbs__with_unicode(rf):
    param_dict = {"qf": u"zaak:Pastorie\xebn, Kleuterscholen"}
    request = rf.get('api/search', param_dict)
    query = NaveESQuery()
    query.build_query_from_request(request)
    user_query = UserQuery(query, num_found=12)
    assert user_query is not None
    assert user_query.breadcrumbs
