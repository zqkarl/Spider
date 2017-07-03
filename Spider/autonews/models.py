#coding:utf-8
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models

# Create your models here.


@python_2_unicode_compatible
class Publisher(models.Model):
    name = models.CharField(u'发布名称', max_length=255)
    url = models.URLField(u'目标地址')
    type = models.CharField(choices=(('yuncaiji_publish', '云采集'),), max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '新闻发布'
        verbose_name_plural = '新闻发布'


@python_2_unicode_compatible
class Task(models.Model):
    task_name = models.CharField(u'任务名称', max_length=255)
    site_name = models.CharField(u'站点名称', max_length=255)
    site_column = models.CharField(u'栏目', max_length=255)
    site_url = models.CharField(u'地址', max_length=255, help_text="网址中的日期部分用'（date,样式,提前的天数）'代替,"
                                                                   "例如(date,yyyy-MM/dd,0),表示为当天的日期，格式为2015-08/27,"
                                                                 "需要循环遍历的地方（loop,首相,末相,相数), 例如(loop,1,10,2)表明循环从1开始到10结束，间隔为2")
    cookie = models.TextField(u'Cookie', blank=True, null=True, help_text="eg:PHPSESSID=123456789;HI_COOKIE=KEY_123456789")
    thread_num = models.IntegerField(u'线程数', default=1)
    seconds = models.IntegerField(u'间隔时间(s)', default=600000)
    switch = models.BooleanField(u'是否开启', default=True)
    publisher = models.ManyToManyField(Publisher, verbose_name="发布方式", null=True, blank=True)

    def __str__(self):  # 在Python3中用 __str__ 代替 __unicode__
        return self.task_name

    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'
        # ordering = ['publish_date']


@python_2_unicode_compatible
class UrlModel(models.Model):
    start_location = models.CharField(u'起始位置', max_length=255, blank=True, null=True)
    end_location = models.CharField(u'结束位置', max_length=255, blank=True, null=True)
    include_words = models.CharField(u'必须包含', max_length=255, blank=True, null=True, help_text="中间以';'来分隔")
    exclude_words = models.CharField(u'不包含', max_length=255, blank=True, null=True, help_text="中间以';'来分隔")
    task = models.OneToOneField(Task)

    def __str__(self):
        return self.task.task_name+"的url模板"

    class Meta:
        verbose_name = "url手动匹配模式"
        verbose_name_plural = 'url手动匹配模式'


@python_2_unicode_compatible
class Model(models.Model):
    tag_name = models.CharField(max_length=255, blank=True, null=True)  # h1
    start_location = models.CharField(u'起始位置', max_length=255, blank=True, null=True)
    end_location = models.CharField(u'结束位置', max_length=255, blank=True, null=True)
    tag_id = models.CharField(max_length=255, blank=True, null=True)  # h1
    tag_attrs = models.CharField(max_length=255, blank=True, null=True, help_text='格式为{"class":"content_title",'
                                                                                  '"style":"text-indent: 2em;"}')
    is_title = models.BooleanField(u'标题', default=False)  # true为标题/false为正文/70
    task = models.ForeignKey(Task)

    def __str__(self):
        return self.task.task_name+"的内容匹配模板"

    class Meta:
        verbose_name = '内容手动匹配模式'
        verbose_name_plural = '内容手动匹配模式'


@python_2_unicode_compatible
class News(models.Model):
    task = models.ForeignKey(Task, verbose_name=u"任务", null=True)
    url = models.URLField()
    title = models.TextField(u'标题')
    content = models.TextField(u'内容')
    keywords = models.CharField(u'关键词', max_length=255, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '新闻'
        verbose_name_plural = '新闻'

