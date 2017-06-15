# libsvm安装说明
1、libsvm下载地址：http://www.csie.ntu.edu.tw/~cjlin/libsvm/ 建议版本为3.21
2、cd libsvm-3.21下
如果是Unix的系统，输入"make",得到libsvm.so.2,将其拷至autonews和autorecog的根目录下
如果是Windows的系统，输入"Makefile",得到libsvm.dll，将其拷至autonews/windows和autorecog/windows的下

# 应用说明
autonews:可视化的网页定时爬取程序
autorecog:提供对网页内容标题和内容分离功能；提供分析文章关键此功能；