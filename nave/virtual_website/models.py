# -*- coding: utf-8 -*-
"""Models for Django Virtual Website App."""
from django.urls import reverse
from django.db import models
from django.http import QueryDict
from django_extensions.db.fields import AutoSlugField
from django_extensions.db.models import TimeStampedModel
from django.utils.translation import ugettext_lazy as _

from nave.void.models import GroupOwned


class VirtualWebsite(TimeStampedModel, GroupOwned):
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
    # fields for diw virtual collection
    diw_header = models.TextField(
        _("diw header"),
        blank=True,
        null=True
    )
    diw_footer = models.TextField(
        _("diw footer"),
        blank=True,
        null=True
    )
    diw_css = models.TextField(
        _("diw css"),
        blank=True,
        null=True
    )
    diw_config = models.TextField(
        _("diw configuration"),
        blank=True,
        null=True
    )
    # This url can be used for navigation
    external_url = models.CharField(
        _("external URL"),
        max_length=512,
        blank=True,
        null=True,
        help_text=_("extern URL voor de virtuele website.")
    )

    class Meta(object):
        verbose_name = _("Virtual Website")
        verbose_name_plural = _("Virtual Websites")

    def __str__(self):
        return self.title

    # work with external URL as well
    # or use relative linking
    def get_absolute_url(self):
        return reverse('virtual_website_detail', kwargs={'slug': self.slug})

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
        super(VirtualWebsite, self).save(*args, **kwargs)


class VirtualWebsitePage(TimeStampedModel, GroupOwned):
    """
    This model holds a custom page for a virtual collection.
    """
    title = models.CharField(
        _("title"),
        max_length=512
    )
    slug = AutoSlugField(
            populate_from=['diw__title', 'title']
    )
    page_body = models.TextField(
        _("page body"),
        blank=True,
        null=True
    )
    diw = models.ForeignKey(
        VirtualWebsite,
        on_delete=models.CASCADE,
        related_name="pages"
    )
    show_search = models.BooleanField(
        _("show search"),
        default=True,
        help_text=_("show search bar on virtual collection page")
    )

    class Meta:
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")
        ordering = ['slug']
