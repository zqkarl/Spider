# coding=utf-8
from __future__ import division  # 计算浮点数

import re

from Spider.autonews.tools.svmutil import *
from spider.autonews import URL


def analyze(url):
    """判断该url是否为内容型url
    :param url 须为URL。URL类"""

    assert type(url) == URL.URL, 'url的类型错误'
    try:
        f1 = len(url.content)  # 锚文本长度
    except TypeError:
        f1 = 0
    if f1 > 100:
        f1 = 1
    else:
        f1 /= 100

    f2 = len(url.url_name)  # URL长度
    if f2 > 120:
        f2 = 1
    else:
        f2 /= 120

    pattern = re.compile(
        '''\S*((((1[6-9]|[2-9]\d)\d{2})([-,/])?(1[02]|0?[13578])([-,/])?([12]\d|3[01]|0?[1-9]))|
        (((1[6-9]|[2-9]\d)\d{2})([-,/])?(1[012]|0?[13456789])([-,/])?([12]\d|30|0?[1-9]))|
        (((1[6-9]|[2-9]\d)\d{2})([-,/])?0?2([-,/])?(1\d|2[0-8]|0?[1-9]))|
        (((1[6-9]|[2-9]\d)(0[48]|[2468][048]|[13579][26])|((16|[2468][048]|[3579][26])00))-0?2-29-))\S*''')
    f3 = 1  # URL是否包含日期
    if re.match(pattern, url.url_name) is None:
        f3 = 0

    beg = url.url_name.rfind("/")+1
    end = url.url_name.find("?")
    if end is -1:
        end = None
    if beg is 0:
        beg = None
    file_name = url.url_name[beg:end]
    f4 = "null"  # 文件名称
    f5 = "null"  # 文件类型
    if file_name.find(".") is not -1:
        f4 = "other"
        if file_name.find("class") is not -1:
            f4 = "class"
        if file_name.find("index") is not -1:
            f4 = "index"
        if file_name.find("list") is not -1:
            f4 = "list"
        if file_name.find("default") is not -1:
            f4 = "default"
        if file_name.find("blog") is not -1:
            f4 = "blog"
        if file_name.find("doc") is not -1:
            f4 = "doc"
        if file_name.find("content") is not -1:
            f4 = "content"
        if file_name.find("article") is not -1:
            f4 = "article"

        f5 = file_name[file_name.find(".")+1:]

    f4d = 0.5
    if f4.find("other") is not -1:
        f4d = 0.7
    if f4.find("null") is not -1:
        f4d = 0.4
    if f4.find("list") is not -1:
        f4d = 0.5
    if f4.find("article") is not -1:
        f4d = 0.9
    if f4.find("doc") is not -1:
        f4d = 0.9
    if f4.find("content") is not -1:
        f4d = 0.6
    if f4.find("blog") is not -1:
        f4d = 0.9
    if f4.find("index") is not -1:
        f4d = 0.1
    if f4.find("default") is not -1:
        f4d = 0.05
    if f4.find("class") is not -1:
        f4d = 0

    f5d = 0.5
    if f5.lower().find("html") is not -1:
        f5d = 0.7
    if f5.lower().find("null") is not -1:
        f5d = 0.6
    if f5.lower().find("jsp") is not -1:
        f5d = 0.3
    if f5.lower().find("asp") is not -1:
        f5d = 0.2
    if f5.lower().find("php") is not -1:
        f5d = 0.2
    if f5.lower().find("aspx") is not -1:
        f5d = 0.2
    if f5.lower() is 'other':
        f5d = 0.4

    f6 = 0  # 是否包含id
    f7 = 0  # 网址所带参数个数
    if url.url_name.find("?") is not -1:
        params = url.url_name[url.url_name.find("?"):]
        if params.find("id") is not -1:
            f6 = 1
        else:
            f6 = 2

        f7 = len(url.url_name.split("&"))

    if f7 > 5:
        f7 = 1
    else:
        f7 /= 5

    # 通过libsvm来判断该url类型
    data_list = []
    row = "0 1:%f 2:%f 3:%f 4:%f 5:%f 6:%f 7:%f" % (f1, f2, f3, f4d, f5d, f6, f7)
    data_list.append(row)
    y, x = svm_read_problem(data_list)
    if sys.platform == 'win32':
        m = svm_load_model("..\url.model")
    else:
        m = svm_load_model("./url.model")
    p_labs, p_acc, p_vals = svm_predict(y, x, m)
    if p_labs[0] == 1.0:
        print "nope"
        return False
    if p_labs[0] == 2.0:
        print "yep"
        return True
    # print "f1= %s f2= %r f3= %r file= %r f4= %r suffix= %r f6 = %d f7= %d" % (f1, f2, f3, file_name, f4, f5, f6, f7)

if __name__ == '__main__':
    a = URL.URL("http://ent.sina.com.cn/y/ygangtai/2016-11-28/doc-ifxyawmm3588266.shtml", "中文")
    analyze(a)
