# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('void', '0004_auto_20150411_1113'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='has_sync_error',
            field=models.BooleanField(default=False, verbose_name='has synchronisation error'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dataset',
            name='sync_error_message',
            field=models.TextField(blank=True, help_text='error message why synchronisation with the triplestore failed.', null=True, verbose_name='synchronisation error'),
            preserve_default=True,
        ),
    ]
