# encoding=utf8

import re
import jieba.analyse
from textrank4zh import TextRank4Keyword


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
                # if i is 5:
                #     break
    return out


def analyze_keywords(text, topK):
    tr4w = TextRank4Keyword()
    tr4w.analyze(text=text, lower=True, window=2)
    keywords = tr4w.get_keywords(10, word_min_len=2)
    out = ""
    for keyword in keywords:
        out += keyword["word"].encode("utf-8")
        out += " "
    print out
    # print '/'.join(tr4w.get_keywords(20, word_min_len=1))

if __name__ == '__main__':
    content = """
    麦卢卡蜂蜜被称为新西兰“国宝”级特产，受到多国消费者的追捧，不过由于缺乏官方标准，市场上鱼龙混杂，让人难辨真假。新西兰第一产业部4月11日公布了麦卢卡蜂蜜的科学定义，以期规范麦卢卡蜂蜜市场。
    第一产业部表示，这一科学定义经过政府和相关专家3年多的研究，可以用于检测麦卢卡蜂蜜真伪。这一科学定义显示，麦卢卡蜂蜜应为蜜蜂采集的麦卢卡植物的花蜜。第一产业部将通过检测蜂蜜中的5种成分来判断其真伪，其中包括对蜂蜜含有的4种化学成分含量的要求以及一种麦卢卡蜂蜜脱氧核糖核酸（DNA）标记。例如，根据这一定义，麦卢卡独花蜜中3-苯基乳酸的含量不少于每公斤400毫克。而在现实中，独花蜜非常难得，第一产业部也对麦卢卡混合花蜜做出界定，在其他标准相同的情况下，混合花蜜的3-苯基乳酸含量在每公斤20毫克至400毫克。
    第一产业部在一份声明中说，对麦卢卡蜂蜜进行定义非常重要，有助于海外监管者对蜂蜜的真伪做出准确判断，以增强国外消费者对产品的信心。现阶段，第一产业部正就这一标准面向公众征求意见。新标准有望在７月正式实施。
    麦卢卡蜂蜜的真伪标准一直是新西兰国内和国际市场争论的焦点。目前，市场上流行的UMF、MGO等麦卢卡蜂蜜的分级体系对于蜂蜜中特有活性抗菌成分的含量界定并不相同，让消费者很难判断。从2014年开始，新西兰第一产业部着手从蜂蜜产品包装、广告等角度规范市场，并组织专家研究麦卢卡蜂蜜真伪标准。（记者 宿亮）</p>
    """
    keywords = analyse_keywords(content, 10)
    print keywords
    # for keyword in keywords:
    #     print (keyword.encode("utf-8"))
    analyze_keywords(content, 22)
