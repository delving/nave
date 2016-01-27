# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django_extensions.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('lod', '0008_auto_20151117_1950'),
    ]

    operations = [
        migrations.CreateModel(
            name='RDFSubjectLookUp',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True)),
                ('subject_uri', models.URLField(unique=True, max_length=512)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'RDF Subject LookUp',
                'verbose_name_plural': 'RDF Subject LookUp',
            },
        ),
    ]
