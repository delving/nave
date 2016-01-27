# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lod', '0006_auto_20151015_2116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cacheresource',
            name='document_uri',
            field=models.URLField(unique=True, verbose_name='document_uri', help_text='The document uri or cache uri '),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='cacheresource',
            name='named_graph',
            field=models.URLField(unique=True, verbose_name='named_graph', help_text='The named graph that this record belongs to'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rdfmodeltest',
            name='document_uri',
            field=models.URLField(unique=True, verbose_name='document_uri', help_text='The document uri or cache uri '),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rdfmodeltest',
            name='named_graph',
            field=models.URLField(unique=True, verbose_name='named_graph', help_text='The named graph that this record belongs to'),
            preserve_default=True,
        ),
    ]
