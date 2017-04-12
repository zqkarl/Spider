#encoding=utf8
from django.contrib import admin
from models import *

# Register your models here.


class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'keywords', 'url')
    search_fields = ('title', 'task__task_name')

admin.site.register(Task)
admin.site.register(Model)
admin.site.register(News, NewsAdmin)
