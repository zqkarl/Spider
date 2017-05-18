# encoding=utf8

import re
import jieba.analyse


def analyse_keywords(sentence, topK):
    """https://github.com/fxsjy/jieba/"""
    keywords = jieba.analyse.extract_tags(sentence, topK)
    out = ""
    i = 0
    for keyword in keywords:
        if keyword is not None and "None" not in keyword:
            keyword = keyword.encode("utf-8")
            if not re.match("^\d+(\.\d+)?$", keyword):
                out += keyword
                out += " "
                i += 1
                if i is 5:
                    break
    return out


if __name__ == '__main__':
    content = """
    5月15日，迪士尼影业CEO鲍勃·伊戈尔向媒体透露，由于近日爆发的病毒危机，使得旗下一部即将上映的大片惨遭被盗。伊戈尔并没有透露影片的名字，
    只是说迪士尼拒绝支付赎金，现在正在跟美国联邦调查局（FBI）合作。虽然电影盗版行业存在已久，索要赎金还真是最近新兴的。
    此前Netflix也曾遭遇类似情况，最后导致《女子监狱》第五季整季片源惨遭泄露。这10集资源比《女子监狱》第五季的首播时间6月9日整整早了6周，
    目前暂不清楚两起事件幕后是否为同一黑客组织所为。上一次黑客操纵的《女子监狱》事件，反而成全了Netflix，
    《女子监狱》资源泄露的新闻成了这部美剧第五季的免费宣传，Netflix的股票在泄露2天后不减反增。特别是泄露的第10集结尾正好留了个大悬念，
    比第四季最后一集还要精彩，而第五季的第11至13集并没有对公众泄露出来。反而促使了许多人上Netflix付费观看后面的3集。"""
    keywords = analyse_keywords(content, 5)
    print keywords
    # for keyword in keywords:
    #     print (keyword.encode("utf-8"))
