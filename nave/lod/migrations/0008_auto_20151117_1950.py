# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lod', '0007_auto_20151102_2135'),
    ]

    operations = [
        migrations.AddField(
            model_name='cacheresource',
            name='acceptance_hash',
            field=models.CharField(unique=True, verbose_name='acceptance hash', help_text='The sha1 content has of the stored ntriples.', blank=True, null=True, max_length=512),
        ),
        migrations.AddField(
            model_name='cacheresource',
            name='acceptance_rdf',
            field=models.TextField(help_text='The rdf stored in the ntriples (nt) format. ', blank=True, verbose_name='acceptance rdf'),
        ),
        migrations.AddField(
            model_name='cacheresource',
            name='acceptance_updated',
            field=models.DateTimeField(help_text='The date the acceptance source was updated', default=django.utils.timezone.now, blank=True, null=True, verbose_name='acceptance update date'),
        ),
        migrations.AddField(
            model_name='cacheresource',
            name='orphaned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='rdfmodeltest',
            name='acceptance_hash',
            field=models.CharField(unique=True, verbose_name='acceptance hash', help_text='The sha1 content has of the stored ntriples.', blank=True, null=True, max_length=512),
        ),
        migrations.AddField(
            model_name='rdfmodeltest',
            name='acceptance_rdf',
            field=models.TextField(help_text='The rdf stored in the ntriples (nt) format. ', blank=True, verbose_name='acceptance rdf'),
        ),
        migrations.AddField(
            model_name='rdfmodeltest',
            name='acceptance_updated',
            field=models.DateTimeField(help_text='The date the acceptance source was updated', default=django.utils.timezone.now, blank=True, null=True, verbose_name='acceptance update date'),
        ),
        migrations.AddField(
            model_name='rdfmodeltest',
            name='orphaned',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='cacheresource',
            name='named_graph',
            field=models.URLField(help_text='The named graph that this record belongs to', verbose_name='named_graph'),
        ),
        migrations.AlterField(
            model_name='cacheresource',
            name='source_updated',
            field=models.DateTimeField(help_text='The date the source was updated', default=django.utils.timezone.now, blank=True, null=True, verbose_name='production update date'),
        ),
        migrations.AlterField(
            model_name='rdfmodeltest',
            name='named_graph',
            field=models.URLField(help_text='The named graph that this record belongs to', verbose_name='named_graph'),
        ),
        migrations.AlterField(
            model_name='rdfmodeltest',
            name='source_updated',
            field=models.DateTimeField(help_text='The date the source was updated', default=django.utils.timezone.now, blank=True, null=True, verbose_name='production update date'),
        ),
    ]
