# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diw', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='diwinstance',
            name='show_config_help',
            field=models.BooleanField(help_text='Show configuration help in the preview. SET to False for production!', default=False, verbose_name='Show configuration help'),
        ),
    ]
