#!/usr/bin/env python
# encoding=utf-8
# util.py
# Copyright (c) 2012, 2012 Kanda.Motohiro@gmail.com
import re
import os
import datetime
import logging
import traceback
import unicodedata
import cgi

# 締め切りなし。当日参加が可能。datetime には、None は入らないので、
# 西暦 9999/12/31 、無効な日付として使う。
# これなら、比較をしたときに、締め切りを過ぎることがないので、よい。
shimekiriNashi = datetime.date.max


#
# 日本語の月日と、 datetime 型の変換
#
def date2Tukihi(d):
    u"""
    これをやると、
    date2Tukihi(datetime.date(2000, 3, 5))
    u'2000\u5e743\u67085\u65e5'
    こうなって、doctest が通らない。コメントの中のユニコードの結果って
    どうやって書くの？
    Failed example:
        date2Tukihi(datetime.date(2000, 3, 5))
    Expected:
        u'2000年3月5日'
    Got:
        u'2000\u5e743\u67085\u65e5'
    """
    if d is None:
        return ""
    year = datetime.date.today().year
    if year == d.year:
        return u"%d月%d日" % (d.month, d.day)
    else:
    # 今年でなければ、年も表示。
        return u"%d年%d月%d日" % (d.year, d.month, d.day)


def tukihi2Date(s, today=None):
    u"""
    >>> today = datetime.date(2012, 8, 17)
    >>> tukihi2Date("2014/5/6")
    datetime.date(2014, 5, 6)
    >>> tukihi2Date("2014 12 31")
    datetime.date(2014, 12, 31)
    >>> tukihi2Date("3/15", today)
    datetime.date(2012, 3, 15)
    >>> tukihi2Date("1 30", today)
    datetime.date(2012, 1, 30)


    >>> tukihi2Date(u"1970年1月1日")
    datetime.date(1970, 1, 1)
    >>> tukihi2Date(u"1月15日", today)
    datetime.date(2012, 1, 15)
    >>> tukihi2Date(u"1970年1月1日")
    datetime.date(1970, 1, 1)
    >>> tukihi2Date(u"3/7", today)
    datetime.date(2012, 3, 7)
    >>> tukihi2Date("3/7", today)
    datetime.date(2012, 3, 7)
    >>> tukihi2Date(u"２０１２年５月4日")
    datetime.date(2012, 5, 4)
    >>> tukihi2Kikan(u"1日", today)
    (datetime.date(2012, 8, 1), datetime.date(2012, 8, 1))
    >>> tukihi2Kikan(u"7日（金）～9日（日）", today)
    (datetime.date(2012, 8, 7), datetime.date(2012, 8, 9))

    """
    dbgprint(s)
    if s is None or s == "" or s == u"なし":
        return None
    if today:
        year = today.year
        month = today.month
    else:
        year = datetime.date.today().year

    # fmt マッチさせるために、前後の空白を除く
    s = s.strip()

    # 全角数字を変換 http://www.nekonomics.jp/2010/12/intunicodedata.html
    if isinstance(s, unicode):
        s = unicodedata.normalize("NFKC", s)

    # 簡単なものを、いくつか試す。
    out = None
    for fmt in "%Y/%m/%d", "%Y %m %d", "%Y-%m-%d", "%m/%d", "%m %d", "%m-%d", \
        "%b. %d, %Y", "%b %d, %Y", "%B. %d, %Y", "%B %d, %Y":
        #print fmt, s
        try:
            out = datetime.datetime.strptime(s, fmt)
        except ValueError, e:
            pass
        else:
            if out is not None:
                break
    # end for fmt

    if out is not None:
        if out.year == 1900:
            return datetime.date(year, out.month, out.day)
        return datetime.date(out.year, out.month, out.day)

    # 3/7 は、３月７日
    m = re.search("(\d{1,2})/(\d{1,2})", s)
    if m:
        month = int(m.group(1))
        day = int(m.group(2))
        return datetime.date(year, month, day)

    m = re.search(u"(\d+)年", s)
    if m is not None:
        year = int(m.group(1))

    m = re.search(u"(\d+)月", s)
    if m is None:
        dbgprint("cannot parse month. " + s)
        return None
    month = int(m.group(1))
    m = re.search(u"(\d+)日", s)
    if m:
        day = int(m.group(1))
    else:
        # 22（土・祝）
        m = re.search(u"(\d+)", s)
        if m is None:
            dbgprint("cannot parse day. " + s)
            return None
        day = int(m.group(1))

    out = datetime.date(year, month, day)
    return out


def tukihi2Kikan(s, today=None):
    """チルダで区切られていれば、開始、終了日として、datetime.date の組を返す。
    なければ、同じ日を２つ返す。"""
    if not u"～" in s:
        d = tukihi2Date(s, today)
        return d, d

    els = s.split(u"～")
    start = tukihi2Date(els[0], today)
    end = tukihi2Date(els[1], today)
    return start, end


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
    def dbgprint(*_):
        pass


def err(handler, message):
    # message は、自分のソースにハードコードしてあるものしか来ないはずだけど。
    message = cgi.escape(message, quote=True)

    els = list(traceback.extract_stack()[-2][:3])
    els[0] = os.path.basename(els[0])
    logging.error(str(els) + unicode(message))
    out = u"""yamanokikaku: ご迷惑をおかけしております。
システムエラーが発生しました。<br>""" + unicode(els) + unicode(message)

    handler.response.headers["Content-Type"] = "text/html; charset=cp932"
    handler.response.out.write("<html><body>%s</body></html>" % \
        out.encode("cp932", "replace"))
    return


def _test():
    verbose = False
    import doctest
    doctest.testmod(verbose=verbose)


def dbgprinttest():
    for i in (5, "hi", ["hi", "ho"], u"あ", [u"薬師岳", u"雲の平"]):
        dbgprint(i)
        logerror(i)


def datetest():
    import sys
    today = datetime.date.today()
    if len(sys.argv) == 2:
        print tukihi2Date(sys.argv[1])
    else:
        print date2Tukihi(today)
        _test()
    """
    print tukihi2Date(u"1970年1月1日")
    print tukihi2Date(u"3/7", today)
    print tukihi2Date("3/7", today)
    print tukihi2Date(u"２０１２年５月4日")
    print tukihi2Kikan(u"1日", today)
    print tukihi2Kikan(u"7日（金）～9日（日）", today)
    """

if __name__ == "__main__":
    datetest()
# eof
