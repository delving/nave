# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VirtualCollection',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True)),
                ('title', models.CharField(verbose_name='title', max_length=512)),
                ('slug', django_extensions.db.fields.AutoSlugField(editable=False, blank=True, populate_from='name')),
                ('body', models.TextField(verbose_name='body', blank=True, null=True)),
                ('query', models.TextField(verbose_name='query', help_text='The full query as used on the search page or search API.', blank=True, null=True)),
                ('oai_pmh', models.BooleanField(verbose_name='published', default=True, help_text='Is this collection publicly available.')),
                ('published', models.BooleanField(verbose_name='published', default=True, help_text='Is this collection publicly available.')),
                ('owner', models.CharField(verbose_name='owner key', max_length=512, help_text='profile ID, user key, etc', blank=True, null=True)),
                ('creator', models.CharField(verbose_name='creator', max_length=512, help_text='name or institution', blank=True, null=True)),
                ('groups', models.ManyToManyField(verbose_name='Group', to='auth.Group', help_text='The groups that have access to this metadata record', blank=True)),
                ('user', models.ForeignKey(verbose_name='Author', to=settings.AUTH_USER_MODEL, blank=True, help_text='The first creator of the object', related_name='virtualcollections', null=True)),
            ],
            options={
                'verbose_name': 'Virtual Collection',
                'verbose_name_plural': 'Virtual Collections',
            },
        ),
    ]
