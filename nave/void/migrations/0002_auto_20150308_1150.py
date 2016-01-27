# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('void', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='edmrecord',
            old_name='production_rdf',
            new_name='source_rdf',
        ),
        migrations.RemoveField(
            model_name='edmrecord',
            name='production_updated',
        ),
        migrations.AddField(
            model_name='edmrecord',
            name='source_updated',
            field=models.DateTimeField(help_text='The date the source was updated', blank=True, default=django.utils.timezone.now, verbose_name='production update date'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='edmrecord',
            name='source_uri',
            field=models.URLField(help_text='If the item is cached this is the original uri where this object is found. It is also saved in the graph as owl:sameAs', null=True, blank=True, verbose_name='source uri'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='acceptance_updated',
            field=models.DateTimeField(null=True, blank=True, verbose_name='acceptance update date'),
            preserve_default=True,
        ),
    ]
