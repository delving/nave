# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.utils.timezone
import django_extensions.db.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('void', '0009_auto_20151102_2135'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProxyMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', blank=True, editable=False)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', blank=True, editable=False)),
                ('user_uri', models.URLField()),
                ('proxy_resource_uri', models.URLField()),
                ('skos_concept_uri', models.URLField()),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('mapping_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'verbose_name': 'Proxy Mapping',
                'verbose_name_plural': 'Proxy Mappings',
            },
        ),
        migrations.CreateModel(
            name='ProxyResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', blank=True, editable=False)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', blank=True, editable=False)),
                ('proxy_uri', models.URLField(unique=True)),
                ('frequency', models.IntegerField(default=0)),
                ('label', models.TextField()),
                ('language', models.CharField(max_length=26, blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Proxy Resource',
                'verbose_name_plural': 'Proxy Resources',
            },
        ),
        migrations.CreateModel(
            name='ProxyResourceField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', blank=True, editable=False)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', blank=True, editable=False)),
                ('property_uri', models.URLField()),
                ('search_label', models.CharField(max_length=56)),
                ('dataset_uri', models.URLField()),
            ],
            options={
                'verbose_name': 'Proxy Resource Field',
                'verbose_name_plural': 'Proxy Resource Field',
            },
        ),
        migrations.AlterField(
            model_name='dataset',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', blank=True, editable=False),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', blank=True, editable=False),
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', blank=True, editable=False),
        ),
        migrations.AlterField(
            model_name='edmrecord',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', blank=True, editable=False),
        ),
        migrations.AddField(
            model_name='proxyresourcefield',
            name='dataset',
            field=models.ForeignKey(blank=True, to='void.DataSet', null=True),
        ),
        migrations.AddField(
            model_name='proxyresource',
            name='dataset',
            field=models.ForeignKey(to='void.DataSet'),
        ),
        migrations.AddField(
            model_name='proxyresource',
            name='proxy_field',
            field=models.ForeignKey(to='void.ProxyResourceField'),
        ),
        migrations.AddField(
            model_name='proxymapping',
            name='proxy_resource',
            field=models.ForeignKey(blank=True, to='void.ProxyResource', null=True),
        ),
        migrations.AddField(
            model_name='proxymapping',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='edmrecord',
            name='proxy_resources',
            field=models.ManyToManyField(to='void.ProxyResource'),
        ),
        migrations.AlterUniqueTogether(
            name='proxyresourcefield',
            unique_together=set([('property_uri', 'dataset_uri')]),
        ),
    ]
