# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lod', '0011_auto_20160516_2038'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sparqlquery',
            name='prefixes',
            field=models.ManyToManyField(blank=True, to='lod.RDFPrefix', verbose_name='prefixes'),
        ),
        migrations.AlterField(
            model_name='usergeneratedcontent',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='usergeneratedcontent',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
