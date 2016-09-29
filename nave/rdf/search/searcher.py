class RDFSearcher():

    def __init__(
        self,
        default_facets=None
    ):
        self.default_facets = default_facets

    @property
    def facet_list(self):
        return []
