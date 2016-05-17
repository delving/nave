# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lod', '0010_auto_20160504_0753'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rdfprefix',
            name='uri',
            field=models.CharField(max_length=256, verbose_name='prefix url'),
        ),
        migrations.AlterField(
            model_name='sparqlquery',
            name='prefixes',
            field=models.ManyToManyField(blank=True, null=True, verbose_name='prefixes', to='lod.RDFPrefix'),
        ),
    ]
