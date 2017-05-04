# coding=utf8

import requests
from bs4 import BeautifulSoup
from bs4 import element

def test():
    html = requests.get("http://politics.people.com.cn/n1/2017/0503/c1001-29251588.html")
    text = html.text
    try:
        text = text.encode(html.encoding).decode("utf8")
    except UnicodeDecodeError:
        text = text.encode(html.encoding).decode("GB18030")
    except UnicodeEncodeError:
        text = text.encode("GB18030").decode("GB18030")
    soup = BeautifulSoup(text, "lxml")

    lines = []
    for child in soup.body.descendants:
        # print ("-------------------------------------")

        if type(child) is element.Tag:
            line = {"tag": child}
            lines.append(line)
        else:
            # print (child)
            pass
    list = getparent(lines)
    last_parent = None
    for i in list:
        if last_parent is i.parent:
            print ("True")
        last_parent = i.parent
        # print (i.parent)
        # print ("-------------------------------------")

def getparent(lines):
    list = []
    for line in lines:
        tag = line['tag']
        if tag.name is "p":
            list.append(tag)
    return list


if __name__ == '__main__':
    test()