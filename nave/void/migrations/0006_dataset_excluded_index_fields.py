# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '__first__'),
        ('void', '0005_auto_20150413_1046'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='excluded_index_fields',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', to='taggit.Tag', verbose_name='Tags', through='taggit.TaggedItem'),
            preserve_default=True,
        ),
    ]
