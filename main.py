#!/usr/bin/env python
# encoding=utf-8
# http://yamanokikaku.appspot.com/main.py
# Copyright (c) 2008, 2012 Kanda.Motohiro@gmail.com
# Licensed under the Apache License, Version 2.0

"""todo
https://developers.google.com/appengine/docs/python/python27/migrate27#appyaml
"""
import os
# use django 1.1 if possible
# http://code.google.com/intl/ja/appengine/docs/python/tools/libraries.html
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library, _library
try:
    use_library('django', '1.2')
except _library.UnacceptableVersionError, e:
    dbgprint(e)
    pass

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
import datetime
from util import *

class Kikaku(db.Model):
    "山行企画"
    no = db.IntegerProperty(required=True) # No. 243
    title = db.StringProperty(required=True) # 薬師岳、雲の平
    rank = db.StringProperty() # C-C-8.5
    start = db.DateProperty(required=True) # 8/8
    end = db.DateProperty() # 8/12
    shimekiri = db.DateProperty(required=True) # 締切日 6/24
    teiin = db.IntegerProperty() # 定員　１０人
    leaders = db.StringListProperty() # リーダー　大友、三浦
    members = db.StringListProperty()

    def detail(self):
        leaders = ",".join(self.leaders)
        if 0 < len(self.members):
            members = ",".join(self.members)
        else:
            members = u""

        return u"リーダー:%s メンバー:%s" % (leaders, members)

    def __repr__(self):
        # 定員、なし。いくらでも受付可能というのは、イレギュラーなので注意。
        if self.teiin == 0:
            teiin = u"なし"
        else:
            teiin = u"%d人" % self.teiin
        if self.start == self.end:
            end = ""
        else:
            end = u"-" + date2Tukihi(self.end)

        # 締切日。指定なし、というのもある。
        if self.shimekiri == shimekiriNashi:
            shimekiri = u"なし"
        else:
            shimekiri = date2Tukihi(self.shimekiri)

        # no は、リンクにするので、ここでは返さない。
        return u"%s %s 期日:%s%s 締切日:%s 定員:%s 現在:%d 人" % \
           (self.title, self.rank, date2Tukihi(self.start),
           end, shimekiri, teiin, len(self.members))
# end class

class Kaiin(db.Model):
    "山岳会の会員"
    no = db.IntegerProperty(required=True) # 会員番号 9000
    name = db.StringProperty(required=True) # 田部井淳子
    openid = db.StringProperty(required=True) # user.nickname
    # 携帯端末の識別番号でログインさせることになるかも。

def openid2KaiinNoAndName(openid):
    "OpenID ニックネームをもらい、会員かどうか見る。"
    query =  db.GqlQuery("SELECT * FROM Kaiin WHERE openid = :1", openid)
    recs = query.fetch(1)
    if recs:
        k = recs[0]
        # どうせ、会員番号と氏名で使うので、ここで name はその形にしておく。
        return k.no, u"%d %s" % (k.no, k.name)
    else:
        # 会員でない人は、番号 -1 を返し、openid nickname をそのまま返す。
        return -1, openid

def getKeyAndUser(handler):
    """申し込みとキャンセルで使われる、ユーザーと企画のキーを返す。
    実は、ニックネームと、データベースレコードの参照になったもの。"""
    key = handler.request.get('key')
    if not key:
        logerr("no key")
        return None, None, None

    try:
        rec = db.get(key)
    except db.BadKeyError:
        logerr("bad key", key)
        return None, None, None

    user = users.get_current_user()
    if not user:
        logerr("no user")
        return None, None, None

    no, name = openid2KaiinNoAndName(user.nickname())

    return rec, no, name

#
# handlers
#
class Apply(webapp.RequestHandler):
    def get(self):
        "山行企画に申し込む。企画のキーが渡る。"
        rec, no, user = getKeyAndUser(self)
        if rec is None:
            err("invalid user/key")
            return

        if user in rec.members:
            err("dup user")
            return

        # 参加者一覧に、このユーザーを追加する。
        rec.members.append(user)
        rec.put()
        dbgprint("%s applied for %d %s" % (user, rec.no, rec.title))
        self.redirect("/detail?key=%s" % rec.key())

class Cancel(webapp.RequestHandler):
    def get(self):
        "山行企画の申し込みをキャンセルする。"
        rec, no, user = getKeyAndUser(self)
        if rec is None:
            err("invalid user/key")
            return

        if not user in rec.members:
            err("no user")
            return

        # 参加者一覧から、このユーザーを削除する。
        i = rec.members.index(user)
        del rec.members[i]
        rec.put()
        dbgprint("%s canceled for %d %s" % (user, rec.no, rec.title))
        self.redirect("/detail?key=%s" % rec.key())

class Detail(webapp.RequestHandler):
    def get(self):
        " 山行企画を表示し、申し込みとキャンセルのリンクをつける。"
        rec, no, user = getKeyAndUser(self)
        if user is None:
            err("invalid user/key")
            return

        moushikomi = ""
        # 自分の申し込みは、取り消せる。
        # 同じ所に２度、申し込みはできない。
        if user in rec.members:
            moushikomi = u"<a href='/cancel?key=%s'>取り消す</a>" % rec.key()

        # 締切日をすぎていれば、申し込みは表示しない。
        #elif rec.shimekiri < datetime.date.today():
        #    moushikomi = ""

        # 定員を超えていれば、おなじく。
        # 定員ゼロは、無限に受付。
        #elif rec.teiin != 0 and rec.teiin <= len(rec.members):
        #    moushikomi = ""
        elif user:
            moushikomi = u"<a href='/apply?key=%s'>申し込む</a>" % rec.key()
        
        body = "No. %d " % rec.no + unicode(rec) + "<br>\n" + \
        rec.detail() + " " + moushikomi + "<br>\n"

        self.response.headers['Content-Type'] = "text/html; charset=Shift_JIS"
        uni = template.render("blank.tmpl", { 'body': body })
        self.response.out.write(uni.encode("cp932", "replace"))

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            body = u"""申し込みなどをするには、
            <a href='/_ah/login_required'>ログイン</a>して下さい。<br>"""
        else:
            no, name = openid2KaiinNoAndName(user.nickname())
            body = u'こんにちわ %s さん。<a href="%s">ログアウト</a><br>' % \
                (name, users.create_logout_url(self.request.uri))

        # 山行企画一覧を表示する。会員には、申し込みもできる詳細ページの
        # リンクを示す。
        # 今は、デモなので、会員名簿がない。ログインしたら、会員とみなす。

        # 今月以降の企画を表示する。
        y = datetime.date.today().year
        m = datetime.date.today().month
        start = datetime.date(y, m, 1)
        # だけど、デモなので、しばらくはこうする。
        start = datetime.date(2012, 8, 1)

        query =  db.GqlQuery("SELECT * FROM Kikaku WHERE start >= :1 ORDER BY start ASC", start)

        kikakuList = []
        for rec in query:
            if user:
                kikaku = "<a href='/detail?key=%s'>No. %d</a> " % (rec.key(), rec.no)
            else:
                kikaku = "No. %d " % rec.no

            kikaku += unicode(rec)
            kikakuList.append(kikaku)

        body += u"<h2>山行案内一覧</h2>" + "<br>\n".join(kikakuList)

        template_values = { 'body': body }

        # ところで、app.yaml に、テンプレートを static と書いてはいけない。
        self.response.headers['Content-Type'] = "text/html; charset=Shift_JIS"
        uni = template.render("main.tmpl", template_values)
        # 丸付き数字は、シフトJIS では見えない。
        self.response.out.write(uni.encode("cp932", "replace"))

#        err(self, "not implemented")

application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/detail', Detail),
    ('/apply', Apply),
    ('/cancel', Cancel)
    ], debug=True)

def main():
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
# eof
