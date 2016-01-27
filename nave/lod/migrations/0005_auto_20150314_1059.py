# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lod', '0004_cacheresource'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cacheresource',
            name='literal_property',
        ),
        migrations.RemoveField(
            model_name='cacheresource',
            name='literal_value',
        ),
        migrations.RemoveField(
            model_name='cacheresource',
            name='spec',
        ),
    ]
