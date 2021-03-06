# coding=utf-8
from __future__ import print_function

"""负责从主网址中爬取出需要的网址"""

import datetime
import logging
import bs4
import requests
import re
import tools.newspublish
from bs4 import BeautifulSoup

from models import *
from .tools.bloomfilter import BloomFilter
from Spider.autonews.tools.svmutil import *
from .object import URL
from ..autorecog.recognize import *
from ..autorecog.keywords import analyse_keywords

import sys
reload(sys)
sys.setdefaultencoding('utf8')

logger = logging.getLogger(__name__)
dirname = path.dirname(path.abspath(__file__))
# 适配不同平台加载模型内容
if sys.platform == 'win32':
    content_model = svm_load_model(path.join(dirname, ".\content.model"))
else:
    content_model = svm_load_model(path.join(dirname, './content.model'))


def crawl(task):
    """根据任务爬取内容的主函数"""
    assert isinstance(task, Task)
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.235'
    }
    cookie = ""
    if task.cookie is not None and task.cookie != "":
        cookie = dict(task.cookie)

    # 对复杂url进行分析处理
    site_url = task.site_url
    site_urls = []
    matchObj1 = re.match(r'.*\(date,(.*?),(.*?)\).*', site_url, re.M | re.I)
    if matchObj1:
        patten = matchObj1.group(1)
        lead = matchObj1.group(2)
        patten = patten.replace("yyyy", "%Y")
        patten = patten.replace("MM", "%m")
        patten = patten.replace("dd", "%d")
        patten = patten.replace("HH", "%H")
        patten = patten.replace("mm", "%M")
        patten = patten.replace("ss", "%S")
        delta = datetime.timedelta(days=int(lead))
        now = datetime.datetime.now() - delta
        patterned_time = now.strftime(patten)  # 计算完偏移量的日期
        site_url = re.sub(r"\(date,(.*?)\)", patterned_time, site_url)

    matchObj = re.match(r'.*\(loop,(.*?),(.*?),(.*?)\).*', site_url, re.M | re.I)
    if matchObj:
        first_num = int(matchObj.group(1))
        last_num = int(matchObj.group(2))
        number_of_phases = int(matchObj.group(3))
        for i in range(first_num, last_num, number_of_phases):
            u = re.sub(r"\(loop,(.*?),(.*?),(.*?)\)", str(i), site_url)
            site_urls.append(u)

    if len(site_urls) is 0:
        site_urls.append(site_url)
    hrefs = []
    url_model = UrlModel.objects.filter(task=task)
    if len(url_model) is 0:  # 判断url是否有模板
        for u in site_urls:
            href = __crawl_urls(u, cookie)  # 获取所有需要采集的地址
            hrefs.extend(href)
    else:
        for u in site_urls:
            href = __crawl_urls_by_model(url_model[0], u, cookie)
            hrefs.extend(href)
    for url in hrefs:
        try:
            r = requests.get(url, headers=header, cookies=cookie)
            logger.info('开始请求%s，返回状态码为%d,当前时间为%s' % (url, r.status_code, datetime.datetime.now()))

            # 如果请求失败重试三次
            if r.status_code != 200:
                i = 0
                while i < 3 and r.status_code != 200:
                    logger.info('正在重试第%d次' % (i + 1))
                    r = requests.get(url, headers=header, cookies=cookie)
                    i += 1
                if r.status_code != 200:
                    raise requests.ConnectionError('网址连接失败'+url)

            html = r.text

            code = "utf8"  # 用于下面对html进行操作
            # 编码判断(待改进)
            try:
                html = html.encode(r.encoding).decode("utf8")
            except UnicodeDecodeError:
                html = html.encode(r.encoding).decode("GB18030")
                code = "utf8"
            except UnicodeEncodeError:
                html = html.encode("GB18030").decode("GB18030")
                code = "GB18030"

            logger.debug("网址%s \n"
                         "编码%s \n"
                         "返回内容%s \n"
                         % (url, r.encoding, html))

            # 分析每条网址并且根据模板识别内容，然后保存数据库并且发送
            ret = __recognize_by_model(html, task, code)
            title = ret.get("title")
            content_html = ret.get("content_html")
            content = ret.get("content")
            if title is None or content_html is None or content_html is '' or title is '':
                ret = traversal(html)
                t = ret.get("title")
                c = ret.get("content_html")
                p = ret.get("content")
                if title is None or title is '':
                    title = t
                if content_html is None or content_html is '':
                    content_html = c
                    content = p
            content_html = __convert_img(content_html, str(url))  # 将文中的图片的相对路径转换为绝对路径
            print (title)
            print (type(content))
            news = News()
            news.task = task
            news.url = url
            news.title = title
            news.content = content_html
            news.keywords = analyse_keywords(content, 5)
            news.save()
            publishers = task.publisher.all()
            print (type(publishers))
            if title is not None and content_html is not None and content_html is not '' and title is not '':
                for publisher in publishers:
                    publisher_type = publisher.type
                    publisher_url = publisher.url
                    r = eval("tools.newspublish."+publisher_type+"(publisher_url, title, content_html, task.site_name, task.site_column, news.keywords)")
                    print (r)
            bf = BloomFilter()
            bf.insert(url)
        except Exception as e:
            print (e)


def __crawl_urls(url, cookie):
    """分析URL下所有可以采集的URL
    :param url:需要分析的URL
    :return set
    """
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHT ML, like Gecko) Chrome/43.0.235'
    }
    r = requests.get(url, headers=header, cookies=cookie)
    content = r.text
    # print r.encoding
    # TODO(qi): 解析编码方式还是不太好，虽然一般够用了，下次有更好的解决方案需要替换掉这段
    try:
        content = content.encode(r.encoding).decode("utf8")
    except UnicodeDecodeError:
        content = content.encode(r.encoding).decode("GB18030")
    except UnicodeEncodeError:
        content = content.encode("GB18030").decode("GB18030")

    soup = BeautifulSoup(content, "html.parser")
    t = soup.find_all("a")

    hrefs = set('')
    bf = BloomFilter()
    for tag in t:
        if tag.get("href") is not None:
            newurl = str(tag.get("href")).strip()
            # 处理不是http开头的各种情况,将相对路径拼接成绝对路径
            if not newurl.startswith("http") and newurl.lower().find("javascript") is -1:
                domain = re.match(r'http(s)?://(.*/)', url, re.M | re.I).group()  # 拿到当前目录
                if newurl.startswith("/"):
                    newurl = domain + newurl
                elif newurl.startswith("./"):
                    newurl.replace("./","")
                    newurl = domain + newurl
                elif newurl.startswith("../"):
                    count = newurl.count("../")
                    while count>0:
                        domain = domain[:len(domain) - 1]
                        domain = re.match(r'http(s)?://(.*/)', domain, re.M | re.I).group()
                        count -= 1
                    newurl = domain + newurl.replace("../", "")
                else: # 剩下的”content_234.html"这种情况
                    newurl = domain + newurl

            # 清理url中最后的#，以及当中的多个///的情况
            newurl = newurl.partition("#")[0]
            newurl = newurl.replace("://", "!!!")
            while newurl.find("//") is not -1:
                newurl = newurl.replace("//", "/")
            newurl = newurl.replace("!!!", "://")

            #TODO 错误识别“http://newspaper.jfdaily.com/xwcb/resfiles/2017-06/19/A0120170619S.pdf”临时处理，以后加（下次看到的话）
            if newurl.find(".pdf") != -1:
                continue

            if "http" in newurl:
                url_o = URL.URL(newurl, unicode(tag.string))

                if url_o.is_contenturl():
                    if not bf.isContains(newurl):
                        # 转跳到下步处理分析内容
                        hrefs.add(newurl)
                        print ("已采集新网址"+url_o.url_name)
                    else:
                        print("该网址已采集过")
    log_hrefs = "已分析网址"+str(url)
    for h in hrefs:
        log_hrefs += "\r\n"
        log_hrefs += h
    logger.info(log_hrefs)
    return hrefs


def __crawl_urls_by_model(url_model, url, cookie):
    """通过模板来获取网址"""
    assert isinstance(url_model, UrlModel)
    start_location = url_model.start_location
    end_location = url_model.end_location
    include_word = url_model.include_words
    include_words = None
    if include_word is not u"":
        include_words = include_word.split(";")
    exclude_word = url_model.exclude_words
    exclude_words = None
    if exclude_word is not u"":
        exclude_words = exclude_word.split(";")
    hrefs = set('')
    bf = BloomFilter()

    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.235'
    }
    r = requests.get(url, headers=header, cookies=cookie)
    content = r.text
    code = r.encoding
    try:
        content = content.encode(r.encoding).decode("utf8")
    except UnicodeDecodeError:
        content = content.encode(r.encoding).decode("GB18030")
    except UnicodeEncodeError:
        content = content.encode("GB18030").decode("GB18030")
        code = "GB18030"

    start_num = 0
    end_num = len(content)
    if start_location is not None and start_location != "":
        start_num = content.find(start_location)
        if start_num == -1:
            start_num = 0
    if end_location is not None and end_location != "":
        end_num = content.find(end_location, start_num)
        if end_num == -1:
            end_num = len(content)
    content = content[start_num:end_num]

    soup = BeautifulSoup(content, "html.parser")
    a_tags = soup.find_all("a")

    for tag in a_tags:
        if tag.get("href") is not None:
            newurl = str(tag.get("href")).strip()
            newurl = newurl.replace("\\","/")
            # 处理不是http开头的各种情况,将相对路径拼接成绝对路径
            if not newurl.startswith("http") and newurl.lower().find("javascript") is -1:
                domain = re.match(r'http(s)?://(.*/)', url, re.M | re.I).group()  # 拿到当前目录
                if newurl.startswith("/"):
                    newurl = domain + newurl
                elif newurl.startswith("./"):
                    newurl.replace("./","")
                    newurl = domain + newurl
                elif newurl.startswith("../"):
                    count = newurl.count("../")
                    while count>0:
                        domain = domain[:len(domain) - 1]
                        domain = re.match(r'http(s)?://(.*/)', domain, re.M | re.I).group()
                        count -= 1
                    newurl = domain + newurl.replace("../", "")
                else: # 剩下的”content_234.html"这种情况
                    newurl = domain + newurl

            # 清理url中最后的#，以及当中的多个///的情况
            newurl = newurl.partition("#")[0]
            newurl = newurl.replace("://", "!!!")
            while newurl.find("//") is not -1:
                newurl = newurl.replace("//", "/")
            newurl = newurl.replace("!!!", "://")

            # url过滤条件
            continue_flag = False
            if include_words is not None and len(include_words) is not 0:
                for word in include_words:
                    if newurl.find(word) is -1:
                        continue_flag = True
                        break
            if exclude_words is not None and len(exclude_words) is not 0:
                for word in exclude_words:
                    if newurl.find(word) is not -1:
                        continue_flag = True
                        break
            if continue_flag:
                continue

            # TODO 错误识别“http://newspaper.jfdaily.com/xwcb/resfiles/2017-06/19/A0120170619S.pdf”临时处理，以后加（以后高兴加的话）
            if newurl.find(".pdf") != -1:
                continue

            if "http" in newurl:
                if not bf.isContains(newurl):
                    # 转跳到下步处理分析内容
                    hrefs.add(newurl)
                    print("已采集新网址" + newurl)
                else:
                    print("该网址已采集过")
    log_hrefs = "已分析网址"+str(url)
    for h in hrefs:
        log_hrefs += "\r\n"
        log_hrefs += h
    logger.info(log_hrefs)
    return hrefs


# def __recognize_content(soup):
#     """识别网页标题和内容"""
#
#     assert isinstance(soup, BeautifulSoup)
#     soup = __clean(soup)
#     title = ""
#     content = ""
#     return title, content


# def __clean(soup):
#     """清理网页噪声"""
#     assert isinstance(soup, BeautifulSoup)
#
#     try:
#         for script in soup.find_all('script'):
#             script.decompose()
#     except TypeError:
#         pass
#     try:
#         for style in soup.find_all('style'):
#             style.decompose()
#     except TypeError:
#         pass
#     try:
#         for meta in soup.find_all('meta'):
#             meta.decompose()
#     except TypeError:
#         pass
#     try:
#         for form in soup.find_all('soup'):
#             form.decompose()
#     except TypeError:
#         pass
#     try:
#         for inputs in soup.find_all('input'):
#             inputs.decompose()
#     except TypeError:
#         pass
#     try:
#         for select in soup.find_all('select'):
#             select.decompse()
#     except TypeError:
#         pass
#     try:
#         for link in soup.find_all('link'):
#             link.decompse()
#     except TypeError:
#         pass
#
#     return soup


def __recognize_by_model(html, task, code):
    """根据模板筛选标题和内容"""
    assert isinstance(task, Task)
    title = ""
    content = ""
    content_html = ""
    models = Model.objects.filter(task_id=task.id)
    for model in models:
        tag_name = model.tag_name
        tag_id = model.tag_id
        tag_attrs = model.tag_attrs
        attrs_dict = {}
        if tag_attrs is not None and tag_attrs != "":
            attrs_dict = eval(tag_attrs)
        is_title = model.is_title

        # 前后文截取
        # html = html.encode("utf-8")
        assert isinstance(html, unicode)
        start = model.start_location
        end = model.end_location
        start_num = 0
        end_num = len(html)
        if start is not None and start != "":
            start_num = html.find(start.decode(code))
            if start_num == -1:
                start_num = 0
        if end is not None and end != "":
            end_num = html.find(end.decode(code), start_num)
            if end_num == -1:
                end_num = len(html)
        html = html[start_num:end_num]
        try:
            html = html.encode("utf8").decode("utf8")
        except UnicodeDecodeError:
            html = html.encode("utf8").decode("GB18030")
        except UnicodeEncodeError:
            html = html.encode("GB18030").decode("GB18030")


        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as e:
            print (e)
            print (html)
        if is_title:
            try:
                title = soup.find(name=tag_name, id=tag_id, attrs=attrs_dict).string
            except AttributeError:
                print ("找不到标题")
        else:
            # TODO(qi): 需要提供图片
            try:
                if tag_name is not u'' and attrs_dict is not {}:
                    content_soups = soup.find_all(name=tag_name, attrs=attrs_dict)
                    # for s in content_soups:
                    #     if str(s.string) is not None and "None" not in str(s.string):
                    #         content += s.get_text()
                    content_html += str(content_soups[0])
                    content += content_soups[0].get_text()
                else:
                    content_html += str(soup)
                    content += soup.get_text()
            except AttributeError:
                print("找不到内容")
            except TypeError:
                print("找不到内容")
    result = {"title": title, "content": content, "content_html": content_html}
    return result


# def __recognize(lines, line_max):
#     """该私有方法为处理数据并调用libsvm识别标题和内容"""
#
#     title = ''  # 存放标题
#     content = ''  # 存放内容
#     content_html = ''  # 存放原生html
#
#     content_flag = False  # 上一条是否为正文，是的话为True，否的话为False
#     tags = []  # 存放所有Tag
#     for line in lines:
#         # print line.get('content')
#         sequence = line.get('sequence')
#         tag = line.get('tag')
#         tag_name = line.get('tag_name')
#         tag_id = line.get('tag_id')
#         tag_class = line.get('tag_class')
#         content_len = line.get('content_len')
#
#         # 如果是紧跟正文的图片则判断为需要的图片
#         if content_flag is True and tag_name == 'img':
#             content_html += line.get('content_html')
#
#         content_flag = False
#         if not tag_name == 'img':
#             f1 = sequence / line_max  # 在队列中的顺序
#
#             f2 = 0.5
#             try:
#                 if tag_name.lower() == "h1":
#                     f2 = 1
#                 if tag_name.lower() == "h2" or tag_name.lower() == "h3":
#                     f2 = 0.90
#                 if tag_name.lower() == "title":
#                     f2 = 0.80
#                 if tag_name.lower() == "div":
#                     f2 = 0.70
#                 if tag_name.lower() == "span":
#                     f2 = 0.30
#                 if tag_name.lower() == "td" or tag_name.lower() == "th":
#                     f2 = 0.20
#                 if tag_name.lower() == "strong":
#                     f2 = 0.15
#                 if tag_name.lower() == "article":
#                     f2 = 0.10
#                 if tag_name.lower() == "p":
#                     f2 = 0
#             except AttributeError:
#                 pass
#
#             f3 = 0.5
#             try:
#                 if tag_id.lower().find("title") is not -1 or tag_class.lower().find("title") is not -1:
#                     f3 = 1
#                 if tag_id.lower().find("headline") is not -1 or tag_class.lower().find("headline") is not -1:
#                     f3 = 0.90
#                 if tag_id.lower().find("pic") is not -1 or tag_class.lower().find("pic") is not -1:
#                     f3 = 0.40
#                 if tag_id.lower().find("content") is not -1 or tag_class.lower().find("content") is not -1:
#                     f3 = 0.30
#                 if tag_id.lower().find("text") is not -1 or tag_class.lower().find("text") is not -1:
#                     f3 = 0.20
#                 if tag_id.lower().find("author") is not -1 or tag_class.lower().find("author") is not -1:
#                     f3 = 0.10
#                 if tag_id.lower().find("editor") is not -1 or tag_class.lower().find("editor") is not -1:
#                     f3 = 0
#             except AttributeError:
#                 pass
#
#             f4 = content_len / 100
#             if f4 > 1:
#                 f4 = 1
#
#             data_list = []
#             row = "0 1:%f 2:%f 3:%f 4:%f" % (f1, f2, f3, f4)
#             # print row
#             data_list.append(row)
#             y, x = svm_read_problem(data_list)
#             # print (os.path.abspath('..'))
#             # m = svm_load_model('./Spider/autonews/content.model')
#             p_labs, p_acc, p_vals = svm_predict(y, x, content_model)
#             if p_labs[0] == 1.0:
#                 title += line.get('content')
#             if p_labs[0] == 2.0:
#                 content_flag = True
#                 content += line.get('content')
#                 content_html += line.get('content_html')
#                 tags.append(tag)
#
#     result = {"title": title, "content": content, "content_html": content_html, "tags": tags}
#     return result


# def traversal(html):
#     soup = BeautifulSoup(html, "lxml")
#     lines = []
#     # 遍历所有节点
#     i = 0
#     for tag in soup.descendants:
#         line = {'sequence': i}
#         i += 1
#         line['tag'] = tag
#         if type(tag) == bs4.element.Tag:
#             try:
#                 # 标签有内容或者是p标签,并且标签的父节点没有p(因为只需要判断到p就可以了,里面的东西都要的)
#                 if (tag.string is not None or tag.name == 'p') and tag.find_parent('p') is None:
#                     line['content_html'] = str(tag)
#                     try:
#                         line['content_len'] = len(tag.string.strip())
#                     except TypeError and AttributeError:
#                         line['content_len'] = 0
#                     content = ''
#                     for string in tag.stripped_strings:
#                         content += string
#                     line['content'] = content
#                     # content = tag.string
#                     line['tag_name'] = tag.name
#                     line['tag_id'] = tag.get("id")
#                     line['tag_class'] = tag.get("class")
#
#                     # p提取其下所有标签的文字
#                     if tag.name == 'p':
#                         content = ''
#                         for string in tag.stripped_strings:
#                             content += string
#                         line['content_len'] = len(content.strip())
#                         line['content'] = content
#                 elif tag.name == 'img':
#                     line['tag_name'] = tag.name
#                     line['content_html'] = str(tag)
#
#             except StopIteration:
#                 pass
#
#         if type(tag) == bs4.element.NavigableString and tag.string.strip() != '':
#             if tag.next_sibling is not None and tag.previous_sibling is not None:
#                 line['content_html'] = str(tag)+"</br>"
#                 line['tag_name'] = 'p'
#                 line['content_len'] = len(unicode(tag).strip())
#                 content = tag.string
#                 line['content'] = content
#
#         # 判断该节点是否为需要的节点
#         if line.get('tag_name') is not None:
#             lines.append(line)  # 在队列尾部插入新数据
#
#     result = __recognize(lines, i)
#     tags = result['tags']
#     if len(tags) > 0:
#         count = 0
#         last_parent = tags[0].parent
#         for t in tags:
#             if t not in last_parent.descendants and t is not None:
#                 last_parent = last_parent.parent
#                 count += 1
#             if count is 3:
#                 last_parent = None
#                 break
#         if last_parent is not None:
#             result['content_html'] = str(last_parent)
#             print ("success: "+str(last_parent))
#
#     return result

def __convert_img(content_html, url):
    """
    将文章中的相对图片路径转换为绝对路径（如果有的化）
    :param content_html: HTML版的正文
    :param url: 文章的地址
    :return content: 将修改完的文章替换
    """
    assert isinstance(content_html, str)
    assert isinstance(url, str)
    try:
        soup = BeautifulSoup(content_html, "html.parser")
    except Exception as e:
        print ("处理图片地址转换失败")
        return content_html
    imgs = soup.find_all(name="img")
    for img in imgs:
        if img.get("src") is not None:
            src = str(img.get("src")).strip()
            src = src.replace("\\","/")
            # 处理不是http开头的各种情况,将相对路径拼接成绝对路径
            if not src.startswith("http") and src.lower().find("javascript") is -1:
                domain = re.match(r'http(s)?://(.*/)', url, re.M | re.I).group()  # 拿到当前目录
                if src.startswith("/"):
                    src = domain + src
                elif src.startswith("./"):
                    src.replace("./", "")
                    src = domain + src
                elif src.startswith("../"):
                    count = src.count("../")
                    while count>0:
                        domain = domain[:len(domain) - 1]
                        domain = re.match(r'http(s)?://(.*/)', domain, re.M | re.I).group()
                        count -= 1
                    src = domain + src.replace("../", "")
                else:  # 剩下的”content_234.html"这种情况
                    src = domain + src
                img['src'] = src
    return str(soup)


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
