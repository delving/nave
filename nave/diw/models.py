from django.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse
from django_extensions.db.fields import AutoSlugField


class DiwInstance(models.Model):
    """
    Basic model for a Delving Instant Website Instance
    """
    name = models.CharField(
            max_length=55,
            help_text=_("Name of the Delving Instant Website Instance (should be descriptive of the end user)"),
            verbose_name=_("DIW Name")
    )

    endpoint = models.CharField(
        max_length=255,
        help_text=_("Base URL of the api"),
        verbose_name=_("Endpoint")
    )

    orig_id = models.CharField(
        max_length=55,
        help_text=_("Nave org-id of the Endpoint domain"),
        verbose_name=_("Nave organization id")
    )

    collection_spec = models.CharField(
        max_length=55,
        help_text=_("The spec of the dataset to be queried"),
        verbose_name=_("Spec")
    )

    data_provider = models.CharField(
        max_length=55,
        help_text=_("The name of the dataprovider"),
        verbose_name=_("Data provider")
    )

    slug = AutoSlugField(populate_from='name')

    class Meta(object):
        verbose_name = _("DIW Instance")
        verbose_name_plural = _("DIW Instances")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('diw_instance', kwargs={'slug': self.slug})


class DiwFacet(models.Model):
    """
    Facets to be retrieved and displayed
    """
    diw = models.ForeignKey(
        DiwInstance,
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

    class Meta:
        verbose_name = _("Facet")
        verbose_name_plural = _("Facets")
        ordering = ['position']


class DiwResultField(models.Model):
    """
    Fields to be displayed with the intial returned results
    """
    diw = models.ForeignKey(
        DiwInstance,
        related_name="resultfields"
    )

    name = models.CharField(
        max_length=55,
        blank=False,
        help_text=_("The desired field to retrieve ie: dc_title, dc_creator, dcterms_provenance"),
        verbose_name=_("Field name")
    )

    label = models.CharField(
        max_length=55,
        blank=True,
        help_text=_("The label to be displayed before the field value - if left blank no label will be displayed (not recommended)"),
        verbose_name=_("Field label")
    )

    position = models.PositiveSmallIntegerField(
        "Position",
        default=0
    )

    class Meta:
        verbose_name = _("Result field")
        verbose_name_plural = _("Result fields")
        ordering = ['position']


class DiwDetailField(models.Model):
    """
    Fields to be displayed on the detail view
    """
    diw = models.ForeignKey(
        DiwInstance,
        related_name="detailfields"
    )

    name = models.CharField(
        max_length=55,
        blank=False,
        help_text=_("The desired field to retrieve ie: dc_title, dc_creator, dcterms_provenance"),
        verbose_name=_("Field name")
    )

    label = models.CharField(
        max_length=55,
        blank=True,
        help_text=_("The label to be displayed before the field value - if left blank no label will be displayed (not recommended)"),
        verbose_name=_("Field label")
    )

    position = models.PositiveSmallIntegerField(
        "position",
        default=0
    )

    class Meta:
        verbose_name = _("Item field")
        verbose_name_plural = _("Item fields")
        ordering = ['position']




