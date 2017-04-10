# coding=utf8

from bitarray import bitarray
import mmh3
from hashlib import md5
import redis
from django_redis import get_redis_connection


# class BloomFilter(object):
#
#     def __init__(self, size, hash_count):
#         self.size = size
#         self.hash_count = hash_count
#         self.bit_array = bitarray(size)
#         self.bit_array.setall(0)
#
#     def add(self, string):
#         for seed in xrange(self.hash_count):
#             result = mmh3.hash(string, seed) % self.size
#             self.bit_array[result] = 1
#
#     def lookup(self, string):
#         for seed in xrange(self.hash_count):
#             result = mmh3.hash(string, seed) % self.size
#             if self.bit_array[result] == 0:
#                 return "Nope"
#         return "Probably"
#
# if __name__ == '__main__':
#     bf = BloomFilter(500000, 7)
#     bf.
#     bf.add("google")
#     bf.add("dog")
#     print bf.lookup("google")
#     print bf.lookup("apple")
#     print bf.lookup("dog")

class SimpleHash(object):
    def __init__(self, cap, seed):
        self.cap = cap
        self.seed = seed

    def hash(self, value):
        ret = 0
        for i in range(len(value)):
            ret += self.seed * ret + ord(value[i])
        return (self.cap - 1) & ret


class BloomFilter(object):
    def __init__(self,
                 blockNum=1,
                 key='bloomfilter'):
        """
        :param host: the host of Redis
        :param port: the port of Redis
        :param db: witch db in Redis
        :param blockNum: one blockNum for about 90,000,000; if you have more strings for filtering, increase it.
        :param key: the key's name in Redis
        :param password: the password of Redis
        """
        self.server = get_redis_connection("default")  # 避免重写配置文件
        self.bit_size = 1 << 31  # Redis的String类型最大容量为512M，现使用256M
        self.seeds = [5, 7, 11, 13, 31, 37, 61]
        self.key = key
        self.blockNum = blockNum
        self.hashfunc = []
        for seed in self.seeds:
            self.hashfunc.append(SimpleHash(self.bit_size, seed))


    def isContains(self, str_input):
        if not str_input:
            return False
        m5 = md5()
        m5.update(str_input)
        str_input = m5.hexdigest()
        ret = True
        name = self.key + str(int(str_input[0:2], 16) % self.blockNum)
        for f in self.hashfunc:
            loc = f.hash(str_input)
            ret = ret & self.server.getbit(name, loc)
        return ret

    def insert(self, str_input):
        m5 = md5()
        m5.update(str_input)
        str_input = m5.hexdigest()
        name = self.key + str(int(str_input[0:2], 16) % self.blockNum)
        for f in self.hashfunc:
            loc = f.hash(str_input)
            self.server.setbit(name, loc, 1)


if __name__ == '__main__':
    """ 第一次运行时会显示 not exists!，之后再运行会显示 exists! """
    bf = BloomFilter()
    bf.insert('4')
    if bf.isContains('3'):   # 判断字符串是否存在
        print 'exists!'
    else:
        print 'not exists!'