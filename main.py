#!/usr/bin/env python
# encoding=utf-8
# http://yamanokikaku.appspot.com/main.py
# Copyright (c) 2008, 2012 Kanda.Motohiro@gmail.com
# Licensed under the Apache License, Version 2.0

"""todo
client.py で、ユニットテスト、カバレッジ。有効な企画のキーを得る。
ログイン状態とする。あるいは、サーバーで、ローカルならバイパスさせる。
なんか、クッキーに入っているのかな。
main テーブル表示する。
参加者の山行履歴
確認のメールを発信。
"""
import os
import wsgiref.handlers
from google.appengine.ext import db
from google.appengine.api import users
import datetime
import webapp2

import settings
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

    def teiinStr(self):
        # 定員、なし。いくらでも受付可能というのは、イレギュラーなので注意。
        if self.teiin == 0:
            return u"なし"
        else:
            return u"%d人" % self.teiin

    def kijitu(self):
        if self.start == self.end:
            end = ""
        else:
            end = u"-" + date2Tukihi(self.end)

        return date2Tukihi(self.start) + end

    def shimekiribi(self):
        # 締切日。指定なし、というのもある。
        if self.shimekiri == shimekiriNashi:
            return u"なし"
        else:
            return date2Tukihi(self.shimekiri)

    def __repr__(self):
        # no は、リンクにするので、ここでは返さない。
        return u"%s %s 期日:%s 締切日:%s 定員:%s 現在:%d 人" % \
           (self.title, self.rank, self.kijitu(),
           self.shimekiribi(), self.teiinStr(), len(self.members))
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
    実は、ニックネームと、データベースレコードの参照になったもの。
    ついでに、エラーがいろいろあるので、最後の戻り値に文字列で返す。
    """
    key = handler.request.get('key')
    if not key:
        logerror("no key")
        return None, None, "no key"

    try:
        rec = db.get(key)
    except db.BadKeyError:
        logerror("bad key", key)
        return None, None, "bad key"

    user = users.get_current_user()
    if not user:
        logerror("no user")
        return None, None, "no user"

    no, name = openid2KaiinNoAndName(user.nickname())

    return rec, no, name

#
# handlers
#
class Apply(webapp2.RequestHandler):
    def get(self):
        "山行企画に申し込む。企画のキーが渡る。"
        rec, no, user = getKeyAndUser(self)
        if rec is None:
            err(self, "invalid user/key " + user)
            return

        if user in rec.members:
            err(self, "dup user")
            return

        # 参加者一覧に、このユーザーを追加する。
        rec.members.append(user)
        rec.put()
        dbgprint("%s applied for %d %s" % (user, rec.no, rec.title))
        self.redirect("/detail?key=%s" % rec.key())

class Cancel(webapp2.RequestHandler):
    def get(self):
        "山行企画の申し込みをキャンセルする。"
        rec, no, user = getKeyAndUser(self)
        if rec is None:
            err(self, "invalid user/key " + user)
            return

        if not user in rec.members:
            err(self, "no user")
            return

        # 参加者一覧から、このユーザーを削除する。
        i = rec.members.index(user)
        del rec.members[i]
        rec.put()
        dbgprint("%s canceled for %d %s" % (user, rec.no, rec.title))
        self.redirect("/detail?key=%s" % rec.key())

class Detail(webapp2.RequestHandler):
    def get(self):
        " 山行企画を表示し、申し込みとキャンセルのリンクをつける。"
        rec, no, user = getKeyAndUser(self)
        if rec is None:
            err(self, "invalid user/key " + user)
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

        render_template_and_write_in_sjis(self, 'blank.tmpl', body)

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            body = u"""申し込みなどをするには、
            <a href='/login'>ログイン</a>して下さい。"""
        else:
            no, name = openid2KaiinNoAndName(user.nickname())
            body = u'こんにちわ %s さん。<a href="%s">ログアウト</a>。' % \
                (name, users.create_logout_url(self.request.uri))

        # 山行企画一覧を表示する。会員には、申し込みもできる詳細ページの
        # リンクを示す。
        # 今は、デモなので、会員名簿がない。ログインしたら、会員とみなす。

        body += u"&nbsp;<a href='/table'>表形式で見る</a><br>" + SankouKikakuIchiran()

        render_template_and_write_in_sjis(self, 'main.tmpl', body)
        return

# end MainPage

def SankouKikakuIchiran(table=False):
    """山行企画の一覧を、ユニコードの HTML で返す。
    table=True のときは、テーブルタグを使う。
    """
    # 今月以降の企画を表示する。
    y = datetime.date.today().year
    m = datetime.date.today().month
    start = datetime.date(y, m, 1)
    # だけど、デモなので、しばらくはこうする。
    start = datetime.date(2012, 6, 1)

    query =  db.GqlQuery("SELECT * FROM Kikaku WHERE start >= :1 ORDER BY start ASC", start)

    user = users.get_current_user()
    kikakuList = []
    for rec in query:
        if user:
            no = "<a href='/detail?key=%s'>No. %d</a> " % (rec.key(), rec.no)
        else:
            no = "No. %d " % rec.no

        if not table:
            kikaku = no + unicode(rec)
        else:
            kikaku = u"""<tr>
            <td>%s</td><td>%s</td><td>%s</td><td>%s</td>
            <td>%s</td><td>%s</td><td>%d</td>
            </tr>""" % \
            (no, rec.title, rec.rank, rec.kijitu(),
            rec.shimekiribi(), rec.teiinStr(), len(rec.members))
        kikakuList.append(kikaku)

    if not table:
        return u"<h2>山行案内一覧</h2>" + "<br>\n".join(kikakuList)
    else:
        return u"<h2>山行案内一覧</h2>" + "<table border=1>" + \
        u"""<tr><th>番号</th><th>名称</th><th>ランク</th><th>期日</th>
        <th>締め切り</th><th>定員</th><th>現在</th></tr>""" + \
        "\n".join(kikakuList) + "</table>"

class Table(webapp2.RequestHandler):
    def get(self):
        body = SankouKikakuIchiran(table=True)
        render_template_and_write_in_sjis(self, 'blank.tmpl', body)
        return

class Login(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            body = u'<a href="%s">ログアウト</a>' % \
                users.create_logout_url(self.request.uri)
        else:
            body = u"お持ちのID でログインください。<br>" + \
            "<p><a href='%s'>google</a></p>" % \
            users.create_login_url(federated_identity='www.google.com/accounts/o8/id') + \
            "<p><a href='%s'>mixi</a></p>" % \
            users.create_login_url(federated_identity='mixi.jp') + \
            "<p><a href='%s'>biglobe</a></p>" % \
            users.create_login_url(federated_identity='openid.biglobe.ne.jp') + \
            "<p><a href='%s'>yahoo</a></p>" % \
            users.create_login_url(federated_identity='yahoo.co.jp')

        render_template_and_write_in_sjis(self, 'blank.tmpl', body +
            u"""他に、ご使用の OpenID プロバイダーがありましたら、ご連絡下さい。
            <br>ご注意。携帯電話からは、うまくログインできないことがあります。
            おそれいりますが、そのときは、パソコン、スマートフォンなどから
            ご利用下さい。""")

class Debug(webapp2.RequestHandler):
    def get(self):
        "デバッグ用に、最初の企画レコードのキーを返す。"
        if self.request.environ.get("SERVER_NAME") != "localhost":
            self.error(404)

        recs =  db.GqlQuery("SELECT * FROM Kikaku").fetch(1)
        if len(recs) == 0:
            key = "None"
        else:
            key = recs[0].key()
        # プレーンテキスト
        self.response.headers['Content-Type'] = "text/plain"
        self.response.out.write("key=%s" % key)

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/login', Login),
    ('/table', Table),
    ('/detail', Detail),
    ('/debug', Debug),
    ('/apply', Apply),
    ('/cancel', Cancel)
    ], debug=True)
#        err(self, "not implemented")
# eof
