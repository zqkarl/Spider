# coding=utf-8
"""负责从主网址中爬取出需要的网址"""

import datetime
import logging
import bs4
import requests
import os
from bs4 import BeautifulSoup

from models import *
from Spider.autonews.tools.bloomfilter import BloomFilter
from Spider.autonews.tools.svmutil import *
from Spider.autonews.object import URL

import sys
reload(sys)
sys.setdefaultencoding('utf8')

logger = logging.getLogger(__name__)


def crawl(task):
    assert isinstance(task, Task)
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.235'
    }

    href = __crawl_urls(task.site_url)  # 获取所有需要采集的地址
    for url in href:
        r = requests.get(url, headers=header)
        logger.info('开始请求%s，返回状态码为%d,当前时间为%s' % (url, r.status_code, datetime.datetime.now()))

        # 如果请求失败重试三次
        if r.status_code != 200:
            i = 0
            while i < 3 and r.status_code != 200:
                logger.info('正在重试第%d次' % (i + 1))
                r = requests.get(url, headers=header)
                i += 1
            if r.status_code != 200:
                raise requests.ConnectionError('网址连接失败')

        content = r.text

        # 编码判断(待改进)
        try:
            content = content.encode(r.encoding).decode("utf8")
        except UnicodeDecodeError:
            content = content.encode(r.encoding).decode("GB18030")
        except UnicodeEncodeError:
            content = content.encode("GB18030").decode("GB18030")

        logger.debug("网址%s \n"
                     "编码%s \n"
                     "返回内容%s \n"
                     % (url, r.encoding, content))

        soup = BeautifulSoup(content, "lxml")

        # TODO(qi): 分析每条网址并且根据模板识别内容，然后保存数据库并且发送
        title, content = __recognize_by_model(soup, task)
        if title is None or content is None or content is '' or title is '':
            t, c = traversal(soup)
            if title is None or title is '':
                title = t
            if content is None or content is '':
                content = c
        bf = BloomFilter()
        # bf.insert(url)
        print title
        print type(content)
        news = News()
        news.task = task
        news.url = url
        news.title = title
        news.content = content
        news.save()


def __crawl_urls(url):
    """分析URL下所有可以采集的URL
    :param url:需要分析的URL
    :return set
    """
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.235'
    }
    r = requests.get(url, headers=header)
    content = r.text
    # print r.encoding
    # TODO(qi): 解析编码方式还是不太好，虽然一般够用了，下次有更好的解决方案需要替换掉这段
    try:
        content = content.encode(r.encoding).decode("utf8")
    except UnicodeDecodeError:
        content = content.encode(r.encoding).decode("GB18030")
    except UnicodeEncodeError:
        content = content.encode("GB18030").decode("GB18030")

    soup = BeautifulSoup(content, "lxml")
    t = soup.find_all("a")

    hrefs = set('')
    bf = BloomFilter()
    for tag in t:
        if tag.get("href") is not None:
            newurl = tag.get("href")
            if str(tag.get("href")).startswith("/") or not str(tag.get("href")).startswith("http"):
                if newurl.lower().find("javascript") is -1:
                    # end = url.find("/", 7)
                    newurl = str(url) + "/" + str(tag["href"])

            # 清理url中最后的#，以及当中的多个///的情况
            newurl = newurl.partition("#")[0]
            newurl = newurl.replace("://", "!!!")
            while newurl.find("//") is not -1:
                newurl = newurl.replace("//", "/")
            newurl = newurl.replace("!!!", "://")

            if newurl.find("http") is not -1:
                url_o = URL.URL(newurl, unicode(tag.string))

                if url_o.is_contenturl():
                    if not bf.isContains(newurl):
                        # 转跳到下步处理分析内容
                        hrefs.add(newurl)
                        print "已采集新网址"+url_o.url_name
                    else:
                        print "该网址已采集过"
    log_hrefs = "已分析网址"+str(url)
    for h in hrefs:
        log_hrefs += "\r\n"
        log_hrefs += h
    logger.info(log_hrefs)
    return hrefs


def __recognize_content(soup):
    """识别网页标题和内容"""

    assert isinstance(soup, BeautifulSoup)
    soup = __clean(soup)
    title = ""
    content = ""
    return title, content


def __clean(soup):
    """清理网页噪声"""
    assert isinstance(soup, BeautifulSoup)

    try:
        for script in soup.find_all('script'):
            script.decompose()
    except TypeError:
        pass
    try:
        for style in soup.find_all('style'):
            style.decompose()
    except TypeError:
        pass
    try:
        for meta in soup.find_all('meta'):
            meta.decompose()
    except TypeError:
        pass
    try:
        for form in soup.find_all('soup'):
            form.decompose()
    except TypeError:
        pass
    try:
        for inputs in soup.find_all('input'):
            inputs.decompose()
    except TypeError:
        pass
    try:
        for select in soup.find_all('select'):
            select.decompse()
    except TypeError:
        pass
    try:
        for link in soup.find_all('link'):
            link.decompse()
    except TypeError:
        pass

    return soup


def __recognize_by_model(soup, task):
    """根据模板筛选标题和内容"""

    assert isinstance(soup, BeautifulSoup)
    assert isinstance(task, Task)
    title = ""
    content = ""
    models = Model.objects.filter(task_id=task.id)
    for model in models:
        tag_name = model.tag_name
        tag_id = model.tag_id
        tag_attrs = model.tag_attrs
        attrs_dict = {}
        if tag_attrs is not None and tag_attrs != "":
            attrs_dict = eval(tag_attrs)
        is_title = model.is_title
        assert isinstance(is_title, int)

        if is_title:
            title = soup.find(name=tag_name, id=tag_id, attrs=attrs_dict).string
        else:
            # TODO(qi): 需要提供图片
            content_soups = soup.find_all(name=tag_name, attrs=attrs_dict)
            for s in content_soups:
                content += str(s)
    return title, content


def __recognize(lines, line_max):
    """该私有方法为处理数据并调用libsvm识别标题和内容"""

    title = ''  # 存放标题
    content = ''  # 存放内容
    content_html = ''  # 存放原生html

    content_flag = False  # 上一条是否为正文，是的话为True，否的话为False
    for line in lines:
        # print line.get('content')
        sequence = line.get('sequence')
        tag_name = line.get('tag_name')
        tag_id = line.get('tag_id')
        tag_class = line.get('tag_class')
        content_len = line.get('content_len')

        print tag_name

        # 如果是紧跟正文的图片则判断为需要的图片
        if content_flag is True and tag_name == 'img':
            content_html += line.get('content_html')

        content_flag = False
        if not tag_name == 'img':
            f1 = sequence / line_max  # 在队列中的顺序

            f2 = 0.5
            try:
                if tag_name.lower() == "h1":
                    f2 = 1
                if tag_name.lower() == "h2" or tag_name.lower() == "h3":
                    f2 = 0.90
                if tag_name.lower() == "title":
                    f2 = 0.80
                if tag_name.lower() == "div":
                    f2 = 0.70
                if tag_name.lower() == "span":
                    f2 = 0.30
                if tag_name.lower() == "td" or tag_name.lower() == "th":
                    f2 = 0.20
                if tag_name.lower() == "strong":
                    f2 = 0.15
                if tag_name.lower() == "article":
                    f2 = 0.10
                if tag_name.lower() == "p":
                    f2 = 0
            except AttributeError:
                pass

            f3 = 0.5
            try:
                if tag_id.lower().find("title") is not -1 or tag_class.lower().find("title") is not -1:
                    f3 = 1
                if tag_id.lower().find("headline") is not -1 or tag_class.lower().find("headline") is not -1:
                    f3 = 0.90
                if tag_id.lower().find("pic") is not -1 or tag_class.lower().find("pic") is not -1:
                    f3 = 0.40
                if tag_id.lower().find("content") is not -1 or tag_class.lower().find("content") is not -1:
                    f3 = 0.30
                if tag_id.lower().find("text") is not -1 or tag_class.lower().find("text") is not -1:
                    f3 = 0.20
                if tag_id.lower().find("author") is not -1 or tag_class.lower().find("author") is not -1:
                    f3 = 0.10
                if tag_id.lower().find("editor") is not -1 or tag_class.lower().find("editor") is not -1:
                    f3 = 0
            except AttributeError:
                pass

            f4 = content_len / 100
            if f4 > 1:
                f4 = 1

            data_list = []
            row = "0 1:%f 2:%f 3:%f 4:%f" % (f1, f2, f3, f4)
            # print row
            data_list.append(row)
            y, x = svm_read_problem(data_list)
            print os.path.abspath('..')
            m = svm_load_model('./Spider/autonews/content.model')
            p_labs, p_acc, p_vals = svm_predict(y, x, m)
            if p_labs[0] == 1.0:
                title += line.get('content')
            if p_labs[0] == 2.0:
                content_flag = True
                content += line.get('content')
                content_html += line.get('content_html')

    # result = {"title": title, "content": content, "content_html": content_html}
    return str(title), str(content_html)


def traversal(soup):

    lines = []
    # 遍历所有节点
    i = 0
    for tag in soup.descendants:
        line = {'sequence': i}
        i += 1
        if type(tag) == bs4.element.Tag:
            try:
                # 标签有内容或者是p标签,并且标签的父节点没有p(因为只需要判断到p就可以了,里面的东西都要的)
                if (tag.string is not None or tag.name == 'p') and tag.find_parent('p') is None:
                    line['content_html'] = str(tag)
                    try:
                        line['content_len'] = len(tag.string.strip())
                    except TypeError and AttributeError:
                        line['content_len'] = 0
                    content = ''
                    for string in tag.stripped_strings:
                        content += string
                    line['content'] = content
                    # content = tag.string
                    line['tag_name'] = tag.name
                    line['tag_id'] = tag.get("id")
                    line['tag_class'] = tag.get("class")

                    # p提取其下所有标签的文字
                    if tag.name == 'p':
                        content = ''
                        for string in tag.stripped_strings:
                            content += string
                        line['content_len'] = len(content.strip())
                        line['content'] = content
                elif tag.name == 'img':
                    line['tag_name'] = tag.name
                    line['content_html'] = str(tag)

            except StopIteration:
                pass

        if type(tag) == bs4.element.NavigableString and tag.string.strip() != '':
            if tag.next_sibling is not None and tag.previous_sibling is not None:
                line['content_html'] = str(tag)+"</br>"
                line['tag_name'] = 'p'
                line['content_len'] = len(unicode(tag).strip())
                content = tag.string
                line['content'] = content

        # 判断该节点是否为需要的节点
        if line.get('tag_name') is not None:
            lines.append(line)  # 在队列尾部插入新数据

    return __recognize(lines, i)


if __name__ == '__main__':
    crawl(1)
    # __crawl_urls("http://www.sina.com.cn")
    # crawl_urls("http://www.163.com")
    # crawl_urls("http://www.qq.com")
    # crawl_urls("http://www.sohu.com")
    # crawl_urls("http://www.kankanews.com")
    #
    # crawl_urls("http://www.people.com.cn")
    # crawl_urls("http://www.gmw.cn")
    # crawl_urls("http://chinese.yonhapnews.co.kr")
    # crawl_urls("https://www.washingtonpost.com")
    # crawl_urls("http://www.thepaper.cn")
