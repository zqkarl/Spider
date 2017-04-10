# coding=utf8

import time
import os
import MySQLdb
import redis
import url_spider
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
from django.conf import settings
from django.core.cache import cache
from models import *
import logging
logging.basicConfig()


scheduler = BackgroundScheduler()
pool = redis.ConnectionPool(host=settings.REDIS["HOST"], port=settings.REDIS["PORT"],
                                password=settings.REDIS.get("PASSWORD"))
store = RedisJobStore(connection_pool=pool)
scheduler.add_jobstore(store, "redis")
scheduler.start()


def add_job():
    tasks = Task.objects.all()
    for task in tasks:
        seconds = task.seconds
        scheduler.add_job(crawl_task, 'interval', seconds=seconds, args=[task])
    scheduler.add_job(test, 'interval', seconds=2, id='my_job_id')
    return scheduler


def test():
    print "ss"
    time.sleep(1)


def crawl_task(task):
    print task.task_name
    url_spider.crawl(task)


def run():
    scheduler = add_job()
    return scheduler


def stop():
    scheduler.remove_job('my_job_id')
    scheduler.shutdown()


def get_runningjobs():
    jobs = scheduler.get_jobs()
    out = ""
    for job in jobs:
        out += str(job)
    return out

if __name__ == '__main__':
    scheduler = add_job()
    assert isinstance(scheduler, BackgroundScheduler)
    time.sleep(5)
    scheduler.shutdown()




# if __name__ == '__main__':
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(test1, 'interval', seconds=6)
#     scheduler.start()
#     print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
#     try:
#         # This is here to simulate application activity (which keeps the main thread alive).
#         while True:
#             time.sleep(2)  # 其他任务是独立的线程执行
#             print('sleep!')
#     except (KeyboardInterrupt, SystemExit):
#         # Not strictly necessary if daemonic mode is enabled but should be done if possible
#         scheduler.shutdown()
#     print('Exit The Job!')