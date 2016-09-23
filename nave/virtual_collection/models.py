# -*- coding: utf-8 -*-
"""

"""
from django.core.urlresolvers import reverse
from django.db import models
from django.http import QueryDict
from django.utils.encoding import python_2_unicode_compatible
from django_extensions.db.fields import AutoSlugField
from django_extensions.db.models import TimeStampedModel
from filer.fields.image import FilerImageField
from django.utils.translation import ugettext_lazy as _

from nave.void.models import GroupOwned


class VirtualCollection(TimeStampedModel, GroupOwned):
    """
    The models holds the information for the Virtual collections
    """
    title = models.CharField(
        _("title"),
        max_length=512
    )
    slug = AutoSlugField(populate_from='title')
    body = models.TextField(
        _("body"),
        blank=True,
        null=True
    )
    query = models.TextField(
        _("query"),
        blank=True,
        null=True,
        help_text=_("The full query as used on the search page or search API.")
    )
    oai_pmh = models.BooleanField(
        _("published"),
        default=True,
        help_text=_("Is this collection publicly available.")
    )
    published = models.BooleanField(
        _("published"),
        default=True,
        help_text=_("Is this collection publicly available.")
    )
    owner = models.CharField(
        _("owner key"),
        max_length=512,
        blank=True,
        null=True,
        help_text=_("profile ID, user key, etc")
    )
    creator = models.CharField(
        _("creator"),
        max_length=512,
        blank=True,
        null=True,
        help_text=_("name or institution")
    )
    #tags = TaggableManager()
    # image = FilerImageField(
    #     _("image"),
    #     blank=True,
    #     null=True,
    #     help_text=_("The image for the virtual collection.")
    # )

    class Meta(object):
        verbose_name = _("Virtual Collection")
        verbose_name_plural = _("Virtual Collections")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('virtual_collection_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        allowed_filters = ["qf=", 'hfq=', "q=", "hqf[]=", "qf[]="]
        if any(key in self.query for key in allowed_filters):
            # create the proper format string
            filter_list = []
            query_dict = QueryDict(query_string=self.query.split("?", maxsplit=1)[-1])
            for k, v in query_dict.items():
                if any([key.startswith(k) for key in allowed_filters]) and v:
                    applied_filter = query_dict.getlist(k)
                    filter_list.extend(applied_filter)
            self.query = ";;;".join(["\"{}\"".format(k) for k in filter_list])
        super(VirtualCollection, self).save(*args, **kwargs)


class VirtualCollectionFacet(models.Model):
    """
    Facets to be retrieved and displayed
    """
    diw = models.ForeignKey(
        VirtualCollection,
        related_name="facets"
    )

    name = models.CharField(
        max_length=55,
        blank=False,
        help_text=_("The desired field to retrieve ie: dc_creator_facet, dc_subject_facet"),
        verbose_name=_("Facet field")
    )

    label = models.CharField(
        max_length=55,
        blank=False,
        help_text=_("The label to appear above the list of retrieved facets"),
        verbose_name=_("Facet header")
    )

    position = models.PositiveSmallIntegerField(
        "Position",
        default=0
    )
    facet_size = models.PositiveSmallIntegerField(
        "Facet-size",
        default=50
    )

    class Meta:
        verbose_name = _("Facet")
        verbose_name_plural = _("Facets")
        ordering = ['position']
