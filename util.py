#!/usr/bin/env python
# encoding=utf-8
# util.py
# Copyright (c) 2012, 2012 Kanda.Motohiro@gmail.com
"""
>>> tukihi2Datetime(u"1970年1月1日")
datetime.date(1970, 1, 1)
>>> tukihi2Datetime(u"1月15日")
datetime.date(2012, 1, 15)
>>> print date2Tukihi(datetime.date(2000, 3, 5))
3月5日
"""
import re
import os
import datetime
import logging
import traceback
#
# 日本語の月日と、 datetime 型の変換
#
def date2Tukihi(d):
    return u"%d月%d日" % (d.month, d.day)

def tukihi2Date(s):
    # 全角　数字は？
    m = re.search(u"(\d+)年", s)
    if m is None:
        year = datetime.date.today().year
    else:
        year = int(m.group(1))

    m = re.search(u"(\d+)月(\d+)日", s)
    month = int(m.group(1))
    day = int(m.group(2))
    d = datetime.date(year, month, day)
    return d

if __debug__:
    def dbgprint(*args):
        items = list(traceback.extract_stack()[-2][:3])
        items[0] = os.path.basename(items[0])
        logging.warn(str(items) + str(args))
else:
    def dbgprint(*args): pass

def _test():
    import doctest
    doctest.testmod(verbose=True)

if __name__ == '__main__':
    dbgprint(5)
    dbgprint("hi")
    dbgprint("hi", "ho")
    dbgprint(u"あ")
    dbgprint(u"薬師岳", u"雲の平")

    #_test()
# eof
