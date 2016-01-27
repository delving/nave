# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django_extensions.db.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0001_initial'),
        ('lod', '0003_auto_20150309_2145'),
    ]

    operations = [
        migrations.CreateModel(
            name='CacheResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('created', django_extensions.db.fields.CreationDateTimeField(editable=False, verbose_name='created', default=django.utils.timezone.now, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(editable=False, verbose_name='modified', default=django.utils.timezone.now, blank=True)),
                ('hub_id', models.CharField(verbose_name='hub id', unique=True, max_length=512, help_text='legacy culture hubId for documents')),
                ('slug', django_extensions.db.fields.AutoSlugField(editable=False, max_length=512, populate_from='hub_id', verbose_name='slug', blank=True)),
                ('document_uri', models.URLField(verbose_name='document_uri', help_text='The document uri or cache uri ')),
                ('named_graph', models.URLField(verbose_name='named_graph', help_text='The named graph that this record belongs to')),
                ('local_id', models.CharField(verbose_name='local identifier', max_length=512, help_text='The local identifier supplied by the provider')),
                ('uuid', django_extensions.db.fields.UUIDField(editable=False, help_text='The unique uuid created on first save', verbose_name='uuid', blank=True)),
                ('source_uri', models.URLField(verbose_name='source uri', help_text='If the item is cached this is the original uri where this object is found. It is also saved in the graph as owl:sameAs', null=True, blank=True)),
                ('source_rdf', models.TextField(verbose_name='production rdf', blank=True, help_text='The rdf retrieved via OAI-PMH from narthex used in production (n3)')),
                ('source_updated', models.DateTimeField(verbose_name='production update date', blank=True, default=django.utils.timezone.now, help_text='The date the source was updated')),
                ('stored', models.BooleanField(verbose_name='stored', default=False)),
                ('spec', models.CharField(verbose_name='spec', max_length=256, null=True, blank=True)),
                ('literal_value', models.CharField(verbose_name='literal value', max_length=256)),
                ('literal_property', models.CharField(verbose_name='literal property', max_length=256)),
                ('groups', models.ManyToManyField(verbose_name='Group', to='auth.Group', blank=True, help_text='The groups that have access to this metadata record')),
                ('user', models.ForeignKey(related_name='cacheresources', null=True, verbose_name='Author', to=settings.AUTH_USER_MODEL, blank=True, help_text='The first creator of the object')),
            ],
            options={
                'get_latest_by': 'modified',
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
