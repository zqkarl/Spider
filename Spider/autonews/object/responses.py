# coding=utf8
import json
import pickle


class BaseResponse(object):

    def __init__(self, status=1, message="success"):
        self.status = status
        self.message = message

    def __str__(self):
        return json.dumps(self.__dict__)


