# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django_extensions.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DiwDetailField',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(verbose_name='Field name', help_text='The desired field to retrieve ie: dc_title, dc_creator, dcterms_provenance', max_length=55)),
                ('label', models.CharField(verbose_name='Field label', help_text='The label to be displayed before the field value - if left blank no label will be displayed (not recommended)', max_length=55, blank=True)),
                ('position', models.PositiveSmallIntegerField(verbose_name='position', default=0)),
            ],
            options={
                'verbose_name': 'Item field',
                'verbose_name_plural': 'Item fields',
                'ordering': ['position'],
            },
        ),
        migrations.CreateModel(
            name='DiwFacet',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(verbose_name='Facet field', help_text='The desired field to retrieve ie: dc_creator_facet, dc_subject_facet', max_length=55)),
                ('label', models.CharField(verbose_name='Facet header', help_text='The label to appear above the list of retrieved facets', max_length=55)),
                ('position', models.PositiveSmallIntegerField(verbose_name='Position', default=0)),
            ],
            options={
                'verbose_name': 'Facet',
                'verbose_name_plural': 'Facets',
                'ordering': ['position'],
            },
        ),
        migrations.CreateModel(
            name='DiwInstance',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(verbose_name='DIW Name', help_text='Name of the Delving Instant Website Instance (should be descriptive of the end user)', max_length=55)),
                ('endpoint', models.CharField(verbose_name='Endpoint', help_text='Base URL of the api', max_length=255)),
                ('orig_id', models.CharField(verbose_name='Nave organization id', help_text='Nave org-id of the Endpoint domain', max_length=55)),
                ('collection_spec', models.CharField(verbose_name='Spec', help_text='The spec of the dataset to be queried', max_length=55)),
                ('data_provider', models.CharField(verbose_name='Data provider', help_text='The name of the dataprovider', max_length=55)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='name', editable=False, blank=True)),
            ],
            options={
                'verbose_name': 'DIW Instance',
                'verbose_name_plural': 'DIW Instances',
            },
        ),
        migrations.CreateModel(
            name='DiwResultField',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(verbose_name='Field name', help_text='The desired field to retrieve ie: dc_title, dc_creator, dcterms_provenance', max_length=55)),
                ('label', models.CharField(verbose_name='Field label', help_text='The label to be displayed before the field value - if left blank no label will be displayed (not recommended)', max_length=55, blank=True)),
                ('position', models.PositiveSmallIntegerField(verbose_name='Position', default=0)),
                ('diw', models.ForeignKey(related_name='resultfields', to='diw.DiwInstance')),
            ],
            options={
                'verbose_name': 'Result field',
                'verbose_name_plural': 'Result fields',
                'ordering': ['position'],
            },
        ),
        migrations.AddField(
            model_name='diwfacet',
            name='diw',
            field=models.ForeignKey(related_name='facets', to='diw.DiwInstance'),
        ),
        migrations.AddField(
            model_name='diwdetailfield',
            name='diw',
            field=models.ForeignKey(related_name='detailfields', to='diw.DiwInstance'),
        ),
    ]
