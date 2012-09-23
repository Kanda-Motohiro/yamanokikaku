#!/usr/bin/env python
# encoding=utf-8
# http://yamanokikaku.appspot.com/main.py
# Copyright (c) 2008, 2012 Kanda.Motohiro@gmail.com
# Licensed under the Apache License, Version 2.0

"""todo
参加者の山行履歴
確認のメールを発信。
バックアップ。
申し込みと取り消しは、履歴として、保存する。
"""
import os
import datetime
import wsgiref.handlers
from google.appengine.ext import db
from google.appengine.api import users
import webapp2

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
        return u"%s %s 期日:%s 締切日:%s 定員:%s 現在:%d人" % \
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

    if rec is None:
        logerror("no record", key)
        return None, None, "no record"

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
        # デモなので、この日付とする。
        elif rec.shimekiri < datetime.date(2012, 9, 1):
            moushikomi = u"""申し込みは締めきりました。<br>
デモのため、現在日付を、９月１日にしています。これより前の締切日の企画は、
申し込みをできなくしてあります。"""

        # 定員を超えていれば、おなじく。
        # 定員ゼロは、無限に受付。
        #elif rec.teiin != 0 and rec.teiin <= len(rec.members):
        #    moushikomi = ""
        elif user:
            moushikomi = u"<a href='/apply?key=%s'>申し込む</a>" % rec.key()
        
        body = "No. %d " % rec.no + unicode(rec) + "<br>\n" + \
            rec.detail() + "<br>\n" + moushikomi + "<br>\n"

        render_template_and_write_in_sjis(self, 'blank.tmpl', body)

class KaiinTouroku(webapp2.RequestHandler):
    def get(self):
        "山岳会の会員番号、氏名と、openid の対応をもらう。"
        user = users.get_current_user()
        # 変だな。ここに来るはずはないのに。
        if not user:
            self.redirect("/login")
            return

        body = u"""あなたの山岳会での会員番号、氏名を入力下さい。<br> 
        <p><form action='/kaiin' method='post' enctype='multipart/form-data'></p>
        <p><input type='text' name='no' size='8'>会員番号</p>
        <p><input type='text' name='name' size='20'> 氏名</p>
        <p><input type='submit' value='登録'></p>
        </form></p>
        これに加えて、緊急連絡先も登録してもらう必要があるでしょう。
        そこは、まだ、作ってありません。"""

        render_template_and_write_in_sjis(self, 'blank.tmpl', body)

    def post(self):
        # 氏名はシフトJIS で来るはず
        self.request.charset = "cp932"
        try:
            # ここで文字コード変換するので、
            name = self.request.get("name")
        except UnicodeDecodeError, e:
            # いちおう、これも試してみよう
            self.request.charset = "utf8"
            try:
                name = self.request.get("name")
            except UnicodeDecodeError, e:
                err(self, "%s" % (e))
                return
            
        no = self.request.get("no")
        if no != "":
            try:
                no = int(no)
            except ValueError, e:
                no = ""

        if no == "" or name == "":
            body = u"""会員番号（半角数字）とご氏名を入力下さい。<br>
            <a href="/kaiin">入力しなおす</a>。<br>
            """
            render_template_and_write_in_sjis(self, 'blank.tmpl', body)
            return

        user = users.get_current_user()
        if not user:
            err(self, "no user at post")
            return

        openid=user.nickname()

        # 会員でない人が、openid アカウントで登録してきたらどうするか。
        # 手元には、有効な会員と氏名の一覧を持たないので、受け入れるしか無い。
        # 少なくとも、１つのアカウントで、１つの会員レコードしか作っては
        # いけない
        # 自分の名前を間違えたので、入れなおし、は拒んではいけない。

        query =  db.GqlQuery("SELECT * FROM Kaiin WHERE openid = :1", openid)
        recs = query.fetch(1)

        # あれば、更新。なければ、作成。
        if recs:
            rec = recs[0]
            dbgprint("changed no %d->%d name %s->%s" % (rec.no, no, rec.name, name))
            rec.no = no
            rec.name = name
        else:
            rec = Kaiin(no=no, name=name, openid=openid)
            dbgprint("new kaiin no %d name %s" % (no, name))

        rec.put()
        self.redirect("/")

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            body = u"""申し込みなどをするには、
            <a href='/login'>ログイン</a>して下さい。"""
        else:
            no, name = openid2KaiinNoAndName(user.nickname())
            body = u'こんにちわ %s さん。申し込み、取り消しをするには、番号をクリックして下さい。&nbsp;<a href="%s">ログアウト</a>。' % \
                (name, users.create_logout_url(self.request.uri))
            if no == -1:
                body += u"""<br><a href="/kaiin">会員番号を入力</a>していただくと、
よりわかりやすい表示になります。"""

        # 山行企画一覧を表示する。会員には、申し込みもできる詳細ページの
        # リンクを示す。
        # 今は、デモなので、会員名簿がない。ログインしたら、会員とみなす。

        body += SankouKikakuIchiran()

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
            no = "<a href='/detail?key=%s'>%d</a> " % (rec.key(), rec.no)
        else:
            no = "%d " % rec.no

        if not table:
            kikaku = "No." + no + unicode(rec)
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
        body = "<p><a href='%s'>google</a></p>" % \
        users.create_login_url(federated_identity='www.google.com/accounts/o8/id') + \
        "<p><a href='%s'>mixi</a></p>" % \
        users.create_login_url(federated_identity='mixi.jp') + \
        "<p><a href='%s'>biglobe</a></p>" % \
        users.create_login_url(federated_identity='openid.biglobe.ne.jp') + \
        "<p><a href='%s'>yahoo</a></p>" % \
        users.create_login_url(federated_identity='yahoo.co.jp')

        render_template_and_write_in_sjis(self, 'login.tmpl', body)

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
    ('/kaiin', KaiinTouroku),
    ('/debug', Debug),
    ('/apply', Apply),
    ('/cancel', Cancel)
    ], debug=True)
#        err(self, "not implemented")
# eof
