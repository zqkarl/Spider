# encoding=utf8
from django.contrib import admin
from models import *

# Register your models here.


class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'keywords', 'url')
    search_fields = ('title', 'task__task_name')


class ModelInline(admin.TabularInline):
    model = Model


class UrlModelInline(admin.TabularInline):
    model = UrlModel


class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'switch')
    fieldsets = (
        ['一般设置', {
            'fields': ('task_name', 'site_name', 'site_column', 'site_url', 'switch', 'publisher',),
        }],
        ['高级设置', {
            'classes': ('collapse',),  # CSS
            'fields': ('cookie', 'thread_num', 'seconds',),
        }])
    inlines = [ModelInline, UrlModelInline]  # Inline



admin.site.register(Task, TaskAdmin)
admin.site.register(News, NewsAdmin)
admin.site.register(Publisher)
