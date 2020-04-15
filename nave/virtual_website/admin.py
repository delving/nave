from django.contrib import admin
from django.forms import ModelForm

import reversion
from suit_ckeditor.widgets import CKEditorWidget
from suit.widgets import AutosizedTextarea

from .models import VirtualWebsite, VirtualWebsitePage


class VirtualWebsiteForm(ModelForm):
    class Meta:
        widgets = {
            'body': CKEditorWidget(editor_options={'startupFocus': True}),
            'diw_header': CKEditorWidget(editor_options={'startupFocus': False}),
            'diw_footer': CKEditorWidget(editor_options={'startupFocus': False}),
            'diw_css': AutosizedTextarea(attrs={'rows': 40, 'class': 'input-xlarge', 'colls': 120}),
            'diw_config': AutosizedTextarea
        }

class VirtualWebsitePageForm(ModelForm):
    class Meta:
        widgets = {
            'page_body': CKEditorWidget(editor_options={'startupFocus': False})
        }


class PageInline(admin.StackedInline):
    form = VirtualWebsitePageForm
    model = VirtualWebsitePage
    fields = ['title', 'page_body', 'show_search']
    extra = 0
    max_num = 12
    # suit_classes = 'suit-tab suit-tab-pages'


class VirtualWebsiteAdmin(reversion.admin.VersionAdmin):
    list_filter = ['user', 'groups']
    filter_horizontal = ('groups',)
    list_display = ('title', 'user')
    form = VirtualWebsiteForm
    inlines = (PageInline,)
    fieldsets = [
        ('', {
            'classes': ('suit-tab', 'suit-tab-algemeen'),
            'fields': ('title',)
        }),
        # ('pages', {
            # 'classes': ('suit-tab', 'suit-tab-pages'),
            # 'fields': ('virtual_website_page__page_body', 'virtual_website_page__show_search')
        # }),
        ('Query', {
            'classes': ('suit-tab', 'suit-tab-algemeen'),
            'fields': ('query',)
        }),
        ('Body', {
            'classes': ('suit-tab', 'suit-tab-algemeen'),
            'fields': ('body',)
        }),
        ('Header', {
            'classes': ('suit-tab', 'suit-tab-algemeen'),
            'fields': ('diw_header',)
        }),
        ('Footer', {
            'classes': ('suit-tab', 'suit-tab-algemeen'),
            'fields': ('diw_footer',)
        }),
        ('CSS', {
            'classes': ('suit-tab', 'suit-tab-config'),
            'fields': ('diw_css',)
        }),
        ('Config', {
            'classes': ('suit-tab', 'suit-tab-config'),
            'fields': ('diw_config',)
        }),

        ('Extra', {
            'classes': ('suit-tab', 'suit-tab-extra'),
            'fields': ('groups', 'user', 'oai_pmh', 'published', 'owner', 'creator')
        })
    ]

    suit_form_tabs = (('algemeen', 'Algemeen'), ('config', 'DIW configuration'),
                      ('page', 'Pages'), ('extra', 'Extra'))



admin.site.register(VirtualWebsite, VirtualWebsiteAdmin)

