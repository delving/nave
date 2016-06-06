# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('virtual_collection', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VirtualCollectionFacet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=55, help_text='The desired field to retrieve ie: dc_creator_facet, dc_subject_facet', verbose_name='Facet field')),
                ('label', models.CharField(max_length=55, help_text='The label to appear above the list of retrieved facets', verbose_name='Facet header')),
                ('position', models.PositiveSmallIntegerField(default=0, verbose_name='Position')),
                ('facet_size', models.PositiveSmallIntegerField(default=50, verbose_name='Facet-size')),
            ],
            options={
                'verbose_name': 'Facet',
                'verbose_name_plural': 'Facets',
                'ordering': ['position'],
            },
        ),
        migrations.AlterField(
            model_name='virtualcollection',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(editable=False, blank=True, populate_from='title'),
        ),
        migrations.AddField(
            model_name='virtualcollectionfacet',
            name='diw',
            field=models.ForeignKey(to='virtual_collection.VirtualCollection', related_name='facets'),
        ),
    ]
