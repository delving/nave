# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RDFPrefix',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from=b'title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('prefix', models.CharField(unique=True, max_length=25, verbose_name='prefix')),
                ('uri', models.URLField(verbose_name='prefix url')),
            ],
            options={
                'verbose_name': 'RDF Prefix',
                'verbose_name_plural': 'RDF Prefixes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SPARQLQuery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from=b'title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('query', models.TextField(verbose_name='SPARQL query')),
                ('prefixes', models.ManyToManyField(to='lod.RDFPrefix', verbose_name='prefixes')),
            ],
            options={
                'verbose_name': 'SPARQL Query',
                'verbose_name_plural': 'SPARQL Queries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SPARQLUpdateQuery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from=b'title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('query', models.TextField(verbose_name='SPARQL query')),
                ('active', models.BooleanField(default=False, help_text='If the SPARQL update query is scheduled for periodic execution.', verbose_name='active')),
                ('prefixes', models.ManyToManyField(to='lod.RDFPrefix', verbose_name='prefixes')),
            ],
            options={
                'verbose_name': 'SPARQL Update Query',
                'verbose_name_plural': 'SPARQL Update Queries',
            },
            bases=(models.Model,),
        ),
    ]
