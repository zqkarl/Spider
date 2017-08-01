# coding=utf8

import time
import os
import redis
import url_spider
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
from django.conf import settings
from tools.svmutil import svm_load_model
from django.core.cache import cache
from models import *
import logging
logging.basicConfig()


scheduler = BackgroundScheduler()
pool = redis.ConnectionPool(host=settings.REDIS["HOST"], port=settings.REDIS["PORT"],
                                password=settings.REDIS.get("PASSWORD"))
# pool = redis.ConnectionPool(host='172.27.61.181', port='6379')
store = RedisJobStore(connection_pool=pool)
scheduler.add_jobstore(store, "redis")
scheduler.start()
print (os.path.abspath('..'))


def add_job():
    tasks = Task.objects.all()
    for task in tasks:
        try:
            seconds = task.seconds
            max_instances = task.thread_num
            task_name = task.task_name
            if task.switch:
                scheduler.add_job(crawl_task, 'interval', id=str(task.id), seconds=seconds, max_instances=max_instances, args=[task],
                                  name=task_name, jobstore="redis")
        except Exception:
            raise
    # scheduler.add_job(test, 'interval', seconds=2, max_instances=3, jobstore="redis")
    return scheduler


def test():
    print "dsdsdsd"


def crawl_task(task):
    print task.task_name
    url_spider.crawl(task)


def run():
    scheduler = add_job()
    return scheduler


def stop():
    scheduler.remove_all_jobs()
    scheduler.shutdown(wait=False)


def get_runningjobs():
    jobs = scheduler.get_jobs()
    return jobs


def get_scheduler():
    return scheduler

if __name__ == '__main__':
    scheduler = add_job()
    assert isinstance(scheduler, BackgroundScheduler)
    time.sleep(10)
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