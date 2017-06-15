# coding=utf8
import json
import pickle


class BaseResponse(object):

    def __init__(self, status=1, message="success"):
        self.status = status
        self.message = message

    def __str__(self):
        return json.dumps(self.__dict__)


class RecognizeResponse(BaseResponse):

    def __init__(self, title="", content="", content_html="", keywords=""):
        super(RecognizeResponse, self).__init__()
        result = {"title":title, "content":content, "content_html":content_html, "keywords":keywords}
        self.result = result

    def __str__(self):
        return json.dumps(self.__dict__)


if __name__ == '__main__':
    a = RecognizeResponse("1","2","2","2")
    a.result["content"] = "3"
    print a