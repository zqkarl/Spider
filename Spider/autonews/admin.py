# encoding=utf8
import schedule
from apscheduler.jobstores.base import JobLookupError
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

    def save_model(self, request, obj, form, change):
        if obj.switch:
            sche = schedule.get_scheduler()
            try:
                sche.remove_job(str(obj.id))
            except JobLookupError:
                pass
            sche.add_job(schedule.crawl_task, 'interval', id=str(obj.id), seconds=obj.seconds, max_instances=obj.thread_num,
                         args=[obj], name=obj.task_name, jobstore="redis")
        obj.save()


admin.site.register(Task, TaskAdmin)
admin.site.register(News, NewsAdmin)
admin.site.register(Publisher)
