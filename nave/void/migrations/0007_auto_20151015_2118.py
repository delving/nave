# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django_extensions.db.fields
import taggit.managers
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('void', '0006_dataset_excluded_index_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='edmrecord',
            name='error_message',
            field=models.TextField(verbose_name='error message', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='edmrecord',
            name='has_store_error',
            field=models.BooleanField(verbose_name='has store error', default=False, help_text='If post save actions have thrown an error.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='edmrecord',
            name='source_hash',
            field=models.CharField(verbose_name='source hash', unique=True, max_length=512, blank=True, help_text='The sha1 content has of the stored ntriples.', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dataset',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dataset',
            name='excluded_index_fields',
            field=taggit.managers.TaggableManager(to='taggit.Tag', blank=True, verbose_name='excluded index fields', help_text='A comma-separated list of tags.', through='taggit.TaggedItem'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dataset',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='source_rdf',
            field=models.TextField(verbose_name='production rdf', blank=True, help_text='The rdf stored in the ntriples (nt) format. '),
            preserve_default=True,
        ),
    ]
