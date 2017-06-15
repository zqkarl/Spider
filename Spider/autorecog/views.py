# coding:utf-8
from django.shortcuts import render
from objects.responses import *
from django.http import HttpResponse
from models import RecognizeResult
import recognize
import keywords
import traceback
# Create your views here.


def news_recognize(request):
    url = request.GET.get("url")
    resp = RecognizeResponse()
    ip = '0.0.0.0'
    if request.META.has_key('HTTP_X_FORWARDED_FOR'):
        ip = request.META['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.META['REMOTE_ADDR']
    try:
        ret = recognize.auto_recognize(url)
        title = ret.get("title")
        content = ret.get("content")
        content_html = ret.get("content_html")
        keys = keywords.analyse_keywords(ret.get("content"), 10)

        resp.status = 1
        resp.message = "success"
        resp.result["title"] = title
        resp.result["content"] = content
        resp.result["keywords"] = keys
        resp.result["content_html"] = content_html

        record = RecognizeResult()
        record.url = url
        record.title = title
        record.content = content
        record.keywords = keys
        record.content_html = content_html
        record.ip = ip
        record.save()

    except Exception as e:
        resp.status = -99
        resp.message = str(e)
        record = RecognizeResult()
        record.url = url
        record.title = str(e)
        record.content = str(traceback.format_exc(e))
        record.ip = ip
        record.save()
    return HttpResponse(resp, content_type="application/json;charset=UTF-8")


def get_keywords(request):
    content = request.POST.get("content")
    topK = request.GET.get("topK")
    keys = keywords.analyse_keywords(content, int(topK))
    return HttpResponse(keys)