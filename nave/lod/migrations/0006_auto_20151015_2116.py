# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django_extensions.db.fields
from django.conf import settings
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lod', '0005_auto_20150314_1059'),
    ]

    operations = [
        migrations.AddField(
            model_name='cacheresource',
            name='error_message',
            field=models.TextField(verbose_name='error message', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cacheresource',
            name='has_store_error',
            field=models.BooleanField(verbose_name='has store error', help_text='If post save actions have thrown an error.', default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cacheresource',
            name='source_hash',
            field=models.CharField(verbose_name='source hash', max_length=512, help_text='The sha1 content has of the stored ntriples.', unique=True, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rdfmodeltest',
            name='error_message',
            field=models.TextField(verbose_name='error message', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rdfmodeltest',
            name='has_store_error',
            field=models.BooleanField(verbose_name='has store error', help_text='If post save actions have thrown an error.', default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rdfmodeltest',
            name='source_hash',
            field=models.CharField(verbose_name='source hash', max_length=512, help_text='The sha1 content has of the stored ntriples.', unique=True, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='cacheresource',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='cacheresource',
            name='groups',
            field=models.ManyToManyField(verbose_name='Group', blank=True, help_text='The groups that have access to this metadata record', related_name='lod_cacheresource_related', to='auth.Group'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='cacheresource',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='cacheresource',
            name='source_rdf',
            field=models.TextField(verbose_name='production rdf', blank=True, help_text='The rdf stored in the ntriples (nt) format. '),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='cacheresource',
            name='user',
            field=models.ForeignKey(verbose_name='Author', blank=True, help_text='The first creator of the object', to=settings.AUTH_USER_MODEL, related_name='lod_cacheresource_related', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rdfmodeltest',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rdfmodeltest',
            name='groups',
            field=models.ManyToManyField(verbose_name='Group', blank=True, help_text='The groups that have access to this metadata record', related_name='lod_rdfmodeltest_related', to='auth.Group'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rdfmodeltest',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rdfmodeltest',
            name='source_rdf',
            field=models.TextField(verbose_name='production rdf', blank=True, help_text='The rdf stored in the ntriples (nt) format. '),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rdfmodeltest',
            name='user',
            field=models.ForeignKey(verbose_name='Author', blank=True, help_text='The first creator of the object', to=settings.AUTH_USER_MODEL, related_name='lod_rdfmodeltest_related', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rdfprefix',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rdfprefix',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resourcecachetarget',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resourcecachetarget',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sparqlquery',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sparqlquery',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sparqlupdatequery',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sparqlupdatequery',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True),
            preserve_default=True,
        ),
    ]
