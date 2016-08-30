# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diw', '0002_diwinstance_show_config_help'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diwinstance',
            name='show_config_help',
            field=models.BooleanField(help_text='Show configuration help in the preview. UN-CHECK/TURN OFF before creating a zip for download', verbose_name='Show configuration help', default=False),
        ),
    ]
