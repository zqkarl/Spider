"""Spider URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from autonews import views as newsview

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'schedule/$', newsview.schedule_view, name="schedule"),
    url(r'^schedule/start/', newsview.schedule_start, name="schedule_start"),
    url(r'^schedule/stop/', newsview.schedule_stop, name="schedule_stop"),
    url(r'^job/del', newsview.job_remove, name="job_del"),
    url(r'^job/pause', newsview.job_pause, name="job_pause"),
    url(r'^job/resume', newsview.job_resume, name="job_resume"),
]

