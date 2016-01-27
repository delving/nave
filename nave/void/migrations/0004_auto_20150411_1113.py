# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('void', '0003_auto_20150411_1101'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='records_in_sync',
            field=models.BooleanField(help_text='Keep records in sync with Narthex', default=False, verbose_name='records in sync'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dataset',
            name='skos_in_sync',
            field=models.BooleanField(help_text='Keep skos mappings in sync with Narthex', default=False, verbose_name='skos in sync'),
            preserve_default=True,
        ),
    ]
