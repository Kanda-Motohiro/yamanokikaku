#!/usr/bin/env python
# encoding=utf-8
# util.py
# Copyright (c) 2012, 2012 Kanda.Motohiro@gmail.com
"""
>>> tukihi2Date(u"1970年1月1日")
datetime.date(1970, 1, 1)
>>> tukihi2Date(u"1月15日")
datetime.date(2012, 1, 15)
>>> print date2Tukihi(datetime.date(2000, 3, 5))
3月5日
"""
import re
import os
import datetime
import logging
import traceback
import unicodedata
from django.template import Context, loader


def render_template_and_write_in_sjis(handler, template_filename, body):
    # ところで、app.yaml に、テンプレートを static と書いてはいけない。
    handler.response.headers['Content-Type'] = "text/html; charset=cp932"

    t = loader.get_template(template_filename)
    uni = t.render(Context({'body': body}))
    # 丸付き数字は、シフトJIS では見えない。
    handler.response.out.write(uni.encode("cp932", "replace"))
    return


def renderKaiinTemplate(handler, logout, kaiin):
    "会員登録のフォームは、置換部分が多くて、特別。"
    if kaiin.seibetsu == u"男":
        male = "checked"
        female = ""
    else:
        female = "checked"
        male = ""

    # これは、既に登録している人にだけ、見せる。
    if kaiin.name == u"未登録":
        unsubscribe = ""
    else:
        unsubscribe = """<a href='/unsubscribe'>
            このサイトへの登録を削除する</a>。"""
        
    handler.response.headers['Content-Type'] = "text/html; charset=cp932"
    t = loader.get_template('kaiin.tmpl')
    uni = t.render(Context({'logout': logout, 'unsubscribe': unsubscribe,
        'kaiin': kaiin,
        'male': male, 'female': female}))
    handler.response.out.write(uni.encode("cp932", "replace"))
    return

# 締め切りなし。当日参加が可能。datetime には、None は入らないので、
# 西暦 9999/12/31 、無効な日付として使う。
# これなら、比較をしたときに、締め切りを過ぎることがないので、よい。
shimekiriNashi = datetime.date.max


#
# 日本語の月日と、 datetime 型の変換
#
def date2Tukihi(d):
    year = datetime.date.today().year
    if year == d.year:
        return u"%d月%d日" % (d.month, d.day)
    else:
    # 今年でなければ、年も表示。
        return u"%d年%d月%d日" % (d.year, d.month, d.day)


def tukihi2Date(s, today=None):
    if today:
        year = today.year
        month = today.month
    else:
        year = datetime.date.today().year

    # 全角数字を変換 http://www.nekonomics.jp/2010/12/intunicodedata.html
    if isinstance(s, unicode):
        s = unicodedata.normalize("NFKC", s)

    # 3/7 は、３月７日
    m = re.search("(\d{1,2})/(\d{1,2})", s)
    if m:
        month = int(m.group(1))
        day = int(m.group(2))
        return datetime.date(year, month, day)

    m = re.search(u"(\d+)年", s)
    if m:
        year = int(m.group(1))

    m = re.search(u"(\d+)月", s)
    if m:
        month = int(m.group(1))
    m = re.search(u"(\d+)日", s)
    if m:
        day = int(m.group(1))
    else:
        # 22（土・祝）
        m = re.search(u"(\d+)", s)
        day = int(m.group(1))

    d = datetime.date(year, month, day)
    return d


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
    els = list(traceback.extract_stack()[-2][:3])
    els[0] = os.path.basename(els[0])
    logging.error(str(els) + unicode(message))
    out = u"""yamanokikaku: ご迷惑をおかけしております。
システムエラーが発生しました。<br>""" + unicode(els) + unicode(message)

    handler.response.headers['Content-Type'] = "text/html; charset=cp932"
    handler.response.out.write('<html><body>%s</body></html>' % \
        out.encode("cp932", "replace"))
    return


def _test():
    import doctest
    doctest.testmod(verbose=True)


def dbgprinttest():
    for i in (5, "hi", ["hi", "ho"], u"あ", [u"薬師岳", u"雲の平"]):
        dbgprint(i)
        logerror(i)


def datetest():
    today = datetime.date(2012, 8, 17)
    print tukihi2Date(u"1970年1月1日")
    print date2Tukihi(today)
    print tukihi2Date(u"3/7", today)
    print tukihi2Date("3/7", today)
    print tukihi2Date(u"２０１２年５月4日")

    print tukihi2Kikan(u"1日", today)
    print tukihi2Kikan(u"7日（金）～9日（日）", today)

if __name__ == '__main__':
    datetest()
    #_test()
# eof
