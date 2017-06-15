# coding:utf8

from os import path
import datetime
import logging
import bs4
import requests
from bs4 import BeautifulSoup
from svmutil import *
import sys
reload(sys)
sys.setdefaultencoding('utf8')
logger = logging.getLogger(__name__)

dirname = path.dirname(path.abspath(__file__))
if sys.platform == 'win32':
    content_model = svm_load_model(path.join(dirname, ".\content.model"))
else:
    content_model = svm_load_model(path.join(dirname, './content.model'))

def auto_recognize(url):
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.235'
    }
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

    html = r.text
    try:
        html = html.encode(r.encoding).decode("utf8")
    except UnicodeDecodeError:
        html = html.encode(r.encoding).decode("GB18030")
    except UnicodeEncodeError:
        html = html.encode("GB18030").decode("GB18030")
    ret = traversal(html)
    return ret


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


def __recognize(lines, line_max):
    """该私有方法为处理数据并调用libsvm识别标题和内容"""

    title = ''  # 存放标题
    content = ''  # 存放内容
    content_html = ''  # 存放原生html

    content_flag = False  # 上一条是否为正文，是的话为True，否的话为False
    tags = []  # 存放所有Tag
    for line in lines:
        # print line.get('content')
        sequence = line.get('sequence')
        tag = line.get('tag')
        tag_name = line.get('tag_name')
        tag_id = line.get('tag_id')
        tag_class = line.get('tag_class')
        content_len = line.get('content_len')

        if tag_name == "h1":
            title = line.get("content")

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
            p_labs, p_acc, p_vals = svm_predict(y, x, content_model)
            if p_labs[0] == 1.0:
                title = line.get('content')
            if p_labs[0] == 2.0:
                content_flag = True
                content += line.get('content')
                content_html += line.get('content_html')
                tags.append(tag)

    result = {"title": title, "content": content, "content_html": content_html, "tags": tags}
    return result


def traversal(html):
    # print (type(html))
    soup = BeautifulSoup(html, "html.parser")
    soup = __clean(soup)
    # print soup.prettify()
    lines = []
    # 遍历所有节点
    i = 0
    for tag in soup.descendants:
        line = {'sequence': i}
        i += 1
        line['tag'] = tag
        if type(tag) == bs4.element.Tag:
            try:
                # 标签有内容或者是p标签,并且标签的父节点没有p(因为只需要判断到p就可以了,里面的东西都要的)
                if (tag.string is not None or tag.name == 'p' or tag.name == 'h1') and tag.find_parent('p') is None:
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

    result = __recognize(lines, i)
    tags = result['tags']
    if len(tags) > 0:
        count = 0
        last_parent = tags[0].parent
        for t in tags:
            if t not in last_parent.descendants and t is not None:
                last_parent = last_parent.parent
                count += 1
            if count is 3:
                last_parent = None
                break
        if last_parent is not None:
            result['content_html'] = str(last_parent)
            # print ("success: "+str(last_parent))
        try:
            result['content'] = last_parent.get_text(strip=True)
        except AttributeError:
            pass
    return result


if __name__ == '__main__':
    print str(auto_recognize("http://sports.163.com/17/0516/12/CKIDIDP100058780.html"))