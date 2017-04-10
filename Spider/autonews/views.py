# coding=utf8
from django.shortcuts import render
from django.http import HttpResponse
from object.responses import BaseResponse
import schedule

# Create your views here.


def schedule_view(request):
    return render(request, "schedule.html", )


def schedule_start(request):
    resp = BaseResponse()
    try:
        schedule.run()
    except Exception, e:
        resp.message = str(e)
    return HttpResponse(resp)


def schedule_stop(request):
    resp = BaseResponse()
    try:
        schedule.stop()
    except Exception, e:
        resp.message = str(e)
    return HttpResponse(resp)


def schedule_jobs(request):
    jobs = schedule.get_runningjobs()
    return HttpResponse(str(jobs))