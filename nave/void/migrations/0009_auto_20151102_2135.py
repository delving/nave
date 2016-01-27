# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('void', '0008_auto_20151025_2118'),
    ]

    operations = [
        migrations.AlterField(
            model_name='edmrecord',
            name='document_uri',
            field=models.URLField(help_text='The document uri or cache uri ', verbose_name='document_uri', unique=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='named_graph',
            field=models.URLField(help_text='The named graph that this record belongs to', verbose_name='named_graph', unique=True),
            preserve_default=True,
        ),
    ]
