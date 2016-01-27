# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('lod', '0002_auto_20150308_1152'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceCacheTarget',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(editable=False, default=django.utils.timezone.now, blank=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(editable=False, default=django.utils.timezone.now, blank=True, verbose_name='modified')),
                ('name', models.CharField(max_length=256, help_text='The name of the remote resource', verbose_name='name')),
                ('base_url', models.URLField(help_text='The base url of the LoD target', verbose_name='base_url', unique=True)),
                ('sparql_endpoint', models.URLField(help_text='The sparql endpoint', blank=True, null=True, verbose_name='sparql endpoint')),
                ('ontology_url', models.URLField(help_text='The link to an RDF version of the Ontology', blank=True, null=True, verbose_name='ontology url')),
            ],
            options={
                'get_latest_by': 'modified',
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='rdfmodeltest',
            name='document_uri',
            field=models.URLField(help_text='The document uri or cache uri ', verbose_name='document_uri'),
            preserve_default=True,
        ),
    ]
