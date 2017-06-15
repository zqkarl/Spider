# coding=utf8

from os import path
from svmutil import *

dirname = path.dirname(path.abspath(__file__))
if sys.platform == 'win32':
    content_model = svm_load_model(path.join(dirname, ".\content.model"))
else:
    content_model = svm_load_model(path.join(dirname, './content.model'))

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
    # logger.info(log_hrefs)
    return hrefs