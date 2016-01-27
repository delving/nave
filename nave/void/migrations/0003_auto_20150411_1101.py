# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('void', '0002_auto_20150308_1150'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='edmrecord',
            options={'verbose_name_plural': 'Metadata Records', 'verbose_name': 'Metadata Record'},
        ),
        migrations.AddField(
            model_name='dataset',
            name='process_key',
            field=models.CharField(help_text='Celery processing key. When present means that a synchronisation process is running', max_length=256, null=True, blank=True, verbose_name='process key'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dataset',
            name='processed_records',
            field=models.IntegerField(default=0, verbose_name='total number of processed records'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dataset',
            name='stay_in_sync',
            field=models.BooleanField(help_text='Force unsynced state with Narthex', verbose_name='stay in sync with narthex', default=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='document_uri',
            field=models.URLField(help_text='The document uri or cache uri ', verbose_name='document_uri'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='groups',
            field=models.ManyToManyField(help_text='The groups that have access to this metadata record', to='auth.Group', related_name='void_edmrecord_related', blank=True, verbose_name='Group'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='user',
            field=models.ForeignKey(related_name='void_edmrecord_related', null=True, to=settings.AUTH_USER_MODEL, verbose_name='Author', help_text='The first creator of the object', blank=True),
            preserve_default=True,
        ),
    ]
