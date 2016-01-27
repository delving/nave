# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.utils.timezone
import django_extensions.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('void', '0010_auto_20151111_1409'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='last_full_harvest_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='edmrecord',
            name='acceptance_hash',
            field=models.CharField(blank=True, unique=True, verbose_name='acceptance hash', null=True, max_length=512, help_text='The sha1 content has of the stored ntriples.'),
        ),
        migrations.AddField(
            model_name='edmrecord',
            name='acceptance_rdf',
            field=models.TextField(verbose_name='acceptance rdf', blank=True, help_text='The rdf stored in the ntriples (nt) format. '),
        ),
        migrations.AddField(
            model_name='edmrecord',
            name='acceptance_updated',
            field=models.DateTimeField(verbose_name='acceptance update date', blank=True, default=django.utils.timezone.now, help_text='The date the acceptance source was updated', null=True),
        ),
        migrations.AddField(
            model_name='edmrecord',
            name='exclude_from_europeana',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='edmrecord',
            name='orphaned',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='named_graph',
            field=models.URLField(verbose_name='named_graph', help_text='The named graph that this record belongs to'),
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='proxy_resources',
            field=models.ManyToManyField(blank=True, to='void.ProxyResource'),
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='source_updated',
            field=models.DateTimeField(verbose_name='production update date', blank=True, default=django.utils.timezone.now, help_text='The date the source was updated', null=True),
        ),
        migrations.AlterField(
            model_name='proxymapping',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='proxymapping',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
        ),
        migrations.AlterField(
            model_name='proxyresource',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='proxyresource',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
        ),
        migrations.AlterField(
            model_name='proxyresourcefield',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='proxyresourcefield',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
        ),
    ]
