# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('void', '0007_auto_20151015_2118'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='edmrecord',
            name='acceptance_mode_active',
        ),
        migrations.RemoveField(
            model_name='edmrecord',
            name='acceptance_rdf',
        ),
        migrations.RemoveField(
            model_name='edmrecord',
            name='acceptance_updated',
        ),
        migrations.AddField(
            model_name='edmrecord',
            name='rdf_in_sync',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='edmrecord',
            name='rdf_sync_error',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
