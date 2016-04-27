import logging

from django.views.generic import DetailView, TemplateView

from .models import VirtualCollection

logger = logging.getLogger(__name__)


# @login_required
class VirtualCollectionDetailView(DetailView):
    template_name = 'landing_page.html'
    context_object_name = 'vc'
    model = VirtualCollection

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(VirtualCollectionDetailView, self).get_context_data(**kwargs)
        return context


class VirtualCollectionSearchView(TemplateView):
    template_name = "search_page.html"
