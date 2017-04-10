#coding=utf8
from django.test import TestCase
from tools import bloomfilter
from models import *
import url_spider
# Create your tests here.


class BloomfilterTest(TestCase):
    def setUp(self):
        task = Task.objects.create(task_name="人民网", site_name="人民网", site_column="国际",
                            site_url="http://world.people.com.cn/")
        Model.objects.create(tag_name="h1", is_title=True, task=task)
        Model.objects.create(tag_name="p", task=task)

    def test_bloom(self):
        bf = bloomfilter.BloomFilter()
        bf.insert('4')
        self.assertEqual(bf.isContains('4'), True)
        self.assertEqual(bf.isContains("safrewfrwqea"), False)
        tasks = Task.objects.all()
        for task in tasks:
            url_spider.crawl(task)
        news = News.objects.all()
        for n in news:
            print n.title
            print n.content
        self.assertEqual(len(news), 2)



