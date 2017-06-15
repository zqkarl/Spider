# encoding=utf8
from django.contrib import admin
from models import *

# Register your models here.


class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'keywords', 'url')
    search_fields = ('title', 'task__task_name')


class ModelInline(admin.TabularInline):
    model = Model


class TaskAdmin(admin.ModelAdmin):
    inlines = [ModelInline]  # Inline


admin.site.register(Task, TaskAdmin)
admin.site.register(Model)
admin.site.register(News, NewsAdmin)
admin.site.register(Publisher)
