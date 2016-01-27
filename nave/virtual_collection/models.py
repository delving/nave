# -*- coding: utf-8 -*- 
"""

"""
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django_extensions.db.models import TimeStampedModel
from filer.fields.image import FilerImageField
from django.utils.translation import ugettext_lazy as _

from void.models import GroupOwned, OaiPmhPublished, EDMRecord


@python_2_unicode_compatible
class VirtualCollection(TimeStampedModel, GroupOwned):
    """
    The models holds the information for the Virtual collections
    """
    title = models.CharField(
        _("title"),
        max_length=512
    )
    description = models.TextField(
        _("description"),
        blank=True,
        null=True
    )
    query = models.TextField(
        _("query"),
        blank=True,
        null=True,
        help_text=_("The full query as used on the search page or search API.")
    )
    oai_pmh = models.IntegerField(
        choices=OaiPmhPublished(),
        verbose_name=_("OAI-PMH"),
        default=OaiPmhPublished.none,
        help_text=_("OAI-PMH harvestable"),
    )
    # description = RichText
    published = models.BooleanField(
        _("published"),
        default=True,
        help_text=_("Is this collection publicly available.")
    )
    automatic_refresh = models.BooleanField(
        _("automatic refresh"),
        default=False,
        help_text=_("Rerun the query periodically.")
    )
    records = models.ManyToManyField(
        EDMRecord,
        through="virtual_collection.models.CollectionMembership"
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
    tags = TaggableManager()
    image = FilerImageField(
        _("image"),
        blank=True,
        null=True,
        help_text=_("The image for the virtual collection.")
    )

    class Meta(object):
        verbose_name = _("Virtual Collection")
        verbose_name_plural = _("Virtual Collections")

    def __str__(self):
        return self.title


class CollectionMembership(TimeStampedModel):
    """
    This is the link model to link EDM records to Virtual collections
    """
    collection = models.ForeignKey(VirtualCollection)
    record = models.ForeignKey(EDMRecord)
    # todo add orderable
