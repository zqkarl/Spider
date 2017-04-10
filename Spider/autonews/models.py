#coding:utf-8
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models

# Create your models here.


@python_2_unicode_compatible
class Task(models.Model):
    task_name = models.CharField(u'任务名称', max_length=255)
    site_name = models.CharField(u'站点名称', max_length=255)
    site_column = models.CharField(u'栏目', max_length=255)
    site_url = models.CharField(u'地址', max_length=255)
    thread_num = models.IntegerField(u'线程数', default=1)
    seconds = models.IntegerField(u'间隔时间(s)', default=600000)
    switch = models.BooleanField(u'是否开启', default=True)

    def __str__(self):  # 在Python3中用 __str__ 代替 __unicode__
        return self.task_name

    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'
        # ordering = ['publish_date']


@python_2_unicode_compatible
class Model(models.Model):
    tag_name = models.CharField(max_length=255, blank=True, null=True)  # h1
    tag_id = models.CharField(max_length=255, blank=True, null=True)  # h1
    tag_attrs = models.CharField(max_length=255, blank=True, null=True)  # {"style":"text-indent: 2em;"}
    is_title = models.BooleanField(u'标题', default=False)  # true为标题/false为正文
    task = models.ForeignKey(Task)

    def __str__(self):
        return self.task.task_name+"的Model"

    class Meta:
        verbose_name = '模型'
        verbose_name_plural = '模型'


@python_2_unicode_compatible
class News(models.Model):
    task = models.ForeignKey(Task, null=True)
    url = models.URLField()
    title = models.TextField()
    content = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '新闻'
        verbose_name_plural = '新闻'

