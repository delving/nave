# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0001_initial'),
        ('lod', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RDFModelTest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(editable=False, verbose_name='created', blank=True, default=django.utils.timezone.now)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(editable=False, verbose_name='modified', blank=True, default=django.utils.timezone.now)),
                ('hub_id', models.CharField(unique=True, max_length=512, verbose_name='hub id', help_text='legacy culture hubId for documents')),
                ('slug', django_extensions.db.fields.AutoSlugField(max_length=512, populate_from='hub_id', editable=False, verbose_name='slug', blank=True)),
                ('document_uri', models.URLField(verbose_name='document_uri', help_text='The document uri ')),
                ('named_graph', models.URLField(verbose_name='named_graph', help_text='The named graph that this record belongs to')),
                ('local_id', models.CharField(verbose_name='local identifier', max_length=512, help_text='The local identifier supplied by the provider')),
                ('uuid', django_extensions.db.fields.UUIDField(editable=False, verbose_name='uuid', blank=True, help_text='The unique uuid created on first save')),
                ('source_uri', models.URLField(verbose_name='source uri', blank=True, null=True, help_text='If the item is cached this is the original uri where this object is found. It is also saved in the graph as owl:sameAs')),
                ('source_rdf', models.TextField(verbose_name='production rdf', blank=True, help_text='The rdf retrieved via OAI-PMH from narthex used in production (n3)')),
                ('source_updated', models.DateTimeField(default=django.utils.timezone.now, verbose_name='production update date', blank=True, help_text='The date the source was updated')),
                ('groups', models.ManyToManyField(to='auth.Group', verbose_name='Group', blank=True, help_text='The groups that have access to this metadata record')),
                ('user', models.ForeignKey(null=True, related_name='rdfmodeltests', to=settings.AUTH_USER_MODEL, verbose_name='Author', blank=True, help_text='The first creator of the object')),
            ],
            options={
                'get_latest_by': 'modified',
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='rdfprefix',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(populate_from='title', editable=False, verbose_name='slug', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sparqlquery',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(populate_from='title', editable=False, verbose_name='slug', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sparqlupdatequery',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(populate_from='title', editable=False, verbose_name='slug', blank=True),
            preserve_default=True,
        ),
    ]
