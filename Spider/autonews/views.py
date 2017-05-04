# coding=utf8
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from object.responses import BaseResponse
import schedule

# Create your views here.


def schedule_view(request):
    jobs = schedule.get_runningjobs()
    return render(request, "schedule.html", {"jobs": jobs})


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
        reload(schedule)
    except Exception, e:
        resp.message = str(e)
    return HttpResponse(resp)


def job_remove(request):
    id = request.GET.get("id_")
    sche = schedule.get_scheduler()
    sche.remove_job(id)
    return redirect(schedule_view)


def job_pause(request):
    id = request.GET.get("id_")
    sche = schedule.get_scheduler()
    sche.pause_job(id)
    return redirect(schedule_view)


def job_resume(request):
    id = request.GET.get("id_")
    sche = schedule.get_scheduler()
    sche.resume_job(id)
    return redirect(schedule_view)