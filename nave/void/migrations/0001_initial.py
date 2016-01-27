# -*- coding: utf-8 -*-


from django.db import models, migrations
import dj.choices.fields
from django.conf import settings
import django.utils.timezone
import django_extensions.db.fields
import void.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DataSet',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(verbose_name='created', blank=True, editable=False, default=django.utils.timezone.now)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', blank=True, editable=False, default=django.utils.timezone.now)),
                ('name', models.CharField(verbose_name='title', max_length=512)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, overwrite=True, editable=False, verbose_name='slug', populate_from='spec')),
                ('spec', models.CharField(max_length=56, help_text='spec name for the dataset', verbose_name='spec name', unique=True)),
                ('document_uri', models.URLField(verbose_name='document_uri', help_text='The document uri ')),
                ('named_graph', models.URLField(verbose_name='named_graph', help_text='The named graph that this record belongs to')),
                ('dataset_type', dj.choices.fields.ChoiceField(verbose_name='Dataset Type', help_text='The type of the dataset', default=1, choices=void.models.DataSetType)),
                ('oai_pmh', dj.choices.fields.ChoiceField(verbose_name='OAI-PMH', help_text='OAI-PMH harvestable', default=1, choices=void.models.OaiPmhPublished)),
                ('published', models.BooleanField(verbose_name='published', default=True, help_text='Is this collection publicly available.')),
                ('data_owner', models.CharField(verbose_name='data_owner', max_length=512)),
                ('total_records', models.IntegerField(verbose_name='total number of records', default=0)),
                ('invalid', models.IntegerField(verbose_name='number of invalid records', default=0)),
                ('valid', models.IntegerField(verbose_name='number of valid records', default=0)),
                ('file_watch_directory', models.FilePathField(allow_files=False, blank=True, verbose_name='file watcher directory', path='/tmp', help_text='The directory where this dataset looks for its digital objects to link', allow_folders=True)),
                ('groups', models.ManyToManyField(verbose_name='Group', blank=True, to='auth.Group', help_text='The groups that have access to this metadata record')),
                ('user', models.ForeignKey(blank=True, related_name='datasets', help_text='The first creator of the object', verbose_name='Author', null=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
                'ordering': ('-modified', '-created'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EDMRecord',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(verbose_name='created', blank=True, editable=False, default=django.utils.timezone.now)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', blank=True, editable=False, default=django.utils.timezone.now)),
                ('hub_id', models.CharField(max_length=512, help_text='legacy culture hubId for documents', verbose_name='hub id', unique=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, max_length=512, verbose_name='slug', populate_from='hub_id')),
                ('uuid', django_extensions.db.fields.UUIDField(blank=True, verbose_name='uuid', editable=False, help_text='The unique uuid created on first save')),
                ('document_uri', models.URLField(verbose_name='document_uri', help_text='The document uri ')),
                ('named_graph', models.URLField(verbose_name='named_graph', help_text='The named graph that this record belongs to')),
                ('local_id', models.CharField(verbose_name='local identifier', help_text='The local identifier supplied by the provider', max_length=512)),
                ('production_rdf', models.TextField(verbose_name='production rdf', blank=True, help_text='The rdf retrieved via OAI-PMH from narthex used in production (n3)')),
                ('production_updated', models.DateTimeField(verbose_name='production update date', blank=True, default='2015-02-12 14:34:01+0000')),
                ('acceptance_rdf', models.TextField(verbose_name='acceptance rdf', blank=True, help_text='The rdf retrieved via OAI-PMH from narthex used in acceptance (n3)')),
                ('acceptance_updated', models.DateTimeField(verbose_name='acceptance update date', blank=True, default='2015-02-12 14:34:01+0000')),
                ('acceptance_mode_active', models.BooleanField(verbose_name='acceptance mode active', default=False, help_text="When set to true, newer records are available in acceptance mode that haven't beenstaged in production.")),
                ('dataset', models.ForeignKey(help_text='the dataset that this record belongs to', related_name='void_edmrecord_related', verbose_name='dataset', to='void.DataSet', related_query_name='record')),
                ('groups', models.ManyToManyField(verbose_name='Group', blank=True, to='auth.Group', help_text='The groups that have access to this metadata record')),
                ('primary_source', models.ForeignKey(blank=True, null=True, help_text='link to primary resource that implements EDMModel base class', to='contenttypes.ContentType')),
                ('user', models.ForeignKey(blank=True, related_name='edmrecords', help_text='The first creator of the object', verbose_name='Author', null=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Metadata Record',
                'verbose_name_plural': 'Metadata Records',
                'get_latest_by': 'modified',
                'ordering': ('-modified', '-created'),
            },
            bases=(models.Model,),
        ),
    ]
