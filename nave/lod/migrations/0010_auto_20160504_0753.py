# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
        ('lod', '0009_rdfsubjectlookup'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserGeneratedContent',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('created', django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True)),
                ('source_uri', models.URLField(verbose_name='RDF source URI')),
                ('link', models.URLField(verbose_name='External link')),
                ('name', models.CharField(max_length=128, verbose_name='name')),
                ('short_description', models.CharField(max_length=512, verbose_name='short description')),
                ('content_type', models.CharField(help_text='The content type of the link, e.g. wikipedia or youtube.', max_length=64, verbose_name='content_type')),
                ('html_summary', models.TextField(help_text='Contains the unfurled HTML from the saved link', verbose_name='html summary', null=True, blank=True)),
                ('published', models.BooleanField(help_text='Should the UGC be published to unauthorised users.', default=True, verbose_name='published')),
                ('groups', models.ManyToManyField(help_text='The groups that have access to this metadata record', related_name='lod_usergeneratedcontent_related', verbose_name='Group', blank=True, to='auth.Group')),
                ('user', models.ForeignKey(help_text='The first creator of the object', related_name='lod_usergeneratedcontent_related', verbose_name='Author', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'verbose_name': 'User Generated Content',
                'verbose_name_plural': 'User Generated Content',
            },
        ),
        migrations.AlterUniqueTogether(
            name='usergeneratedcontent',
            unique_together=set([('source_uri', 'link')]),
        ),
    ]
