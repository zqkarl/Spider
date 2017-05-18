#coding:utf-8
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models

# Create your models here.


@python_2_unicode_compatible
class RecognizeResult(models.Model):
    url = models.CharField(max_length=255)
    title = models.CharField(max_length=255, null=True)
    content_html = models.TextField(null=True)
    content = models.TextField(null=True)
    keywords = models.CharField(max_length=255, null=True)
    ip = models.GenericIPAddressField()
    get_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "识别记录"