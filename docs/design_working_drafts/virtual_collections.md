# Virtual Collections User Story

## Story

A user that has admin rights, who  wants to highlight a slice of records from all the records currently searchable. 
He creates the search with a query and optional facets. He then copies everything after the '?' from the URL and goes 
to the admin section. There he selects the virtual collection tab and creates a new virtual collection. 

He gives it a title and pastes the url in the  query field. Then he creates the description of the virtual Collection
in a WYSIWYG field. The WYSIWYG field can be fully styled and include images. When needed the HTML should be able to be 
manipulated directly. A short description can be added to describe the goal of the virtual collection. 

Optionally, he can also select or create some tags that are shared with the DataSet model. The tags should be searchable 
and be used as facets or filter.

If no FacetFields are specified the default FacetFields from the settings are used. The custom FacetFields should be 
to able to have their own labels and the order of presentation should be able to be specified.

When the user saves the collection, he should be able to go to the url and see the WYSIWYG page as the landing page
for this collection. When he does a search he is taken to the search page relative to the landing page. Here he sees
the search results and the optional facets he selected. The query from the model should be a hidden query and not be 
present in the bread-crumbs or facet links. In other words, the query is injected into the QueryObject in the backend 
when creating the NaveESQuery object and is not visible anywhere else.

An empty search should launch a query for all records in the virtual collection. 

When a search result is selected, a fold-out shows (reusing unmodified functionality from the default search page) and 
when the detail page is selected it is again relative to the collections landingpage. The 'returns to results' should also
navigate back to the search Virtual Collection search page.

In the search and detail page for the virtual collection, you should see at least the title of the virtual collection 
with a link back to its landing page. Ideally, there should be a more link that shows the owner and short description. 

For developers or aggregators, a dedicated search and  OAI-PMH api is available.  The search should use the same search 
class that is used for PMH but then with the JSON and XML renderers before the HTML renderer. No additional functionality 
should be developed for this. The OAI-PMH api should use the Elastic Search backend to page over the search results, 
but then render only the results from the Virtual Collection query. The standard OAIProvider in 'oaipmh.py' uses the 
Django ORM back-end for retrieving the PMH results. However, it is designed as an Abstract Class so key element can be 
overwritten in a ESOAIProvider sub-class. For DCN and BrabantCloud, there are already use-cases in place where they want
to offer virtual collections as end-point for PMH or as end-point for a DiW. During indexing a `_modified` field should 
be added to the 'meta' section of the 'es_actions' so that the PMH results can be filtered and ordered by 'last modified date'


When you go to the '/virtual-collections/' url you should get a list of all the publicly available virtual collections.
It should list the title and owner of the virtual collection, when a link is clicked it should take you to the 
virtual collection landing page. 

## URls

    * /virtual-collection/ => list all collections
    * /virtual-collection/{slug} => HTML page from WYSIWYG with search bar
    * /virtual-collection/{slug}/search => HTML search page 
    * /virtual-collection/{slug}/hub_id => HTML detail page rendered using the normal Detail Page rendering 
    * /virtual-collection/{slug}/api => api search page
    * /virtual-collection/{slug}/oai-pmh => the oai-pmh interface for just this collection

## Components

    * Virtual Collections app (since this is used by multiple customers it should be a top-level app)
    * apps.py
        * include the human readable name for this App. See void for an example
    * models.py 
        * VirtualCollection Model 
    * views.py
        * LandingPageView enherited from template view
        * sub-class of SearchListApiView for html search and api view
    * urls.py
        * the urls listed in the URLs section
    * templates
        * landing_page.html 
        * ? custom base search page (to show virtual collection title)
        * ? custom base detail page (to show virtual collection title)
        * virtual-collections-list.html (the list of publicly available virtual collections)
    * oaipmh.py
        * the subclass of OAIProvider that uses ES as back-end 

## Changes outside the VirtualCollections App

    * update the RDFModel class to include `_modified` timestamp in the es_action meta section
    * Add tags support to DataSet model that can be reused in the VirtualCollection model
    * update the RDFModel class to index the tags as 'collection_tag' in the system section
    * include the urls.py from the virtual-collections in the 'nave/urls.py'

## Data Model

Fields:

    * title: CharacterField 256
    * slug
    * query: TextField
    * short description: CharacterField
    * owner/creator: CharacterField
    * description: WYSIWYG field
    * tags
    * related model: FacetFields
    * available as pmh: BooleanField (default: true)
    * available as api: BooleanField (default: true)
    * public: BooleanField (default: true)
    * ? thumbnail: for list view 

## Development best practices

    * develop in a feature branch using git flow
    * write the unit tests using py.test
    * documentation should follow the google python documentation standard guidelines
    * __init__.py should be used for module level documentation
