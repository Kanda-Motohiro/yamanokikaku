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

#
# エラーメッセージのログ、応答
#
def logerror(*args):
    els = list(traceback.extract_stack()[-2][:3])
    els[0] = os.path.basename(els[0])
    try:
        logging.error(str(els) + str(args))
    except UnicodeDecodeError:
        logging.error(str(els) + unicode(args))

if __debug__:
    def dbgprint(*args):
        els = list(traceback.extract_stack()[-2][:3])
        els[0] = os.path.basename(els[0])
        try:
            logging.debug(str(els) + str(args))
        except UnicodeDecodeError:
            logging.debug(str(els) + unicode(args))
else:
    def dbgprint(*args): pass

def err(handler, message):
    els = list(traceback.extract_stack()[-2][:3])
    els[0] = os.path.basename(els[0])
    logging.error(str(els) + unicode(message))
    out = u"""yamanokikaku: ご迷惑をおかけしております。
システムエラーが発生しました。<br>""" + unicode(els) + unicode(message)

    handler.response.out.write('<html><body>%s</body></html>' % out)
    return

def _test():
    import doctest
    doctest.testmod(verbose=True)

if __name__ == '__main__':
    for i in (5, "hi", ["hi", "ho"], u"あ", [u"薬師岳", u"雲の平"]):
        dbgprint(i)
        logerror(i)

    print tukihi2Date(u"1970年1月1日")
    print date2Tukihi(datetime.date(2000, 3, 5))
# eof
