# coding=utf-8

import requests
import datetime
import mod_config


def yuncaiji_publish(title, content, news_site, news_column, tags, news_type="text-image"):
    params = {"title": title, "content": content, "newsSite": news_site, "newsColumn": news_column,
              "newsType": news_type, "newsdate": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
              "source": news_site, "tags": tags}
    post_url = mod_config.get_config("post", key="yuncaiji_url")
    r = requests.post(post_url, params)
    return r.text

if __name__ == '__main__':
    r = yuncaiji_publish("title", "content", "新浪排行", "社会新闻", "www")
    print (r)