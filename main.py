#!/usr/bin/env python
# encoding=utf-8
# http://yamanokikaku.appspot.com/main.py
# Copyright (c) 2008, 2012 Kanda.Motohiro@gmail.com

"""todo
エクセルファイルから、CSVにして、バルクロード。
openid nickname から、会員番号にする。
こんにちわ https://me.yahoo.co.jp/a/OivdX2luJ7QBA6dN6NksAguJIZUPFCbaOOM- さん。
http://blairconrad.wordpress.com/ server error on openid login
"""
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
import os
import datetime
from util import *

# use django 1.1 if possible
# http://code.google.com/intl/ja/appengine/docs/python/tools/libraries.html
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library, _library
try:
    use_library('django', '1.1')
except _library.UnacceptableVersionError, e:
    dbgprint(e)
    pass

# http://d.hatena.ne.jp/gonsuzuki/20090129/1233298532
# send shift-jis page
webapp.template.register_template_library('sjisfilter')

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

    def __repr__(self):
        leaders = ",".join(self.leaders)
        if 0 < len(self.members):
            members = ",".join(self.members)
        else:
            members = u""

        # 定員、なし。いくらでも受付可能というのは、イレギュラーなので注意。
        if self.teiin == 0:
            teiin = u"なし"
        else:
            teiin = u"%d人" % self.teiin
        if self.start == self.end:
            end = ""
        else:
            end = u"-" + date2Tukihi(self.end)

        return u"No.%d %s %s 期日:%s%s 締切日:%s 定員:%s<br>\
        リーダー:%s メンバー:%s" % \
           (self.no, self.title, self.rank, date2Tukihi(self.start),
           end, date2Tukihi(self.shimekiri), teiin,
           leaders, members)
# end class

def imanoKikakuItiran():
    "今の山行企画一覧をリストで返す。"
    out = []
    query =  db.GqlQuery("""SELECT * FROM Kikaku ORDER BY no DESC""")

    for rec in query:
        out.append(unicode(rec))
    return out

def getUserAndKey(handler):
    """申し込みとキャンセルで使われる、ユーザーと企画のキーを返す。
    実は、ニックネームと、データベースレコードの参照になったもの。"""
    user = users.get_current_user()
    if not user:
        logerr("no user")
        return None, None

    key = handler.request.get('key')
    if not key:
        logerr("no key")
        return None, None

    try:
        rec = db.get(key)
    except db.BadKeyError:
        logerr("bad key", key)
        return None, None

    return user.nickname(), rec

#
# handlers
#
class Apply(webapp.RequestHandler):
    def get(self):
        "山行企画に申し込む。企画のキーが渡る。"
        user, rec = getUserAndKey(self)
        if user is None:
            err("invalid user/key")
            return

        if user in rec.members:
            err("dup user")
            return

        # 参加者一覧に、このユーザーを追加する。
        rec.members.append(user)
        rec.put()
        dbgprint("%s applied for %s" % (user, rec.title))
        self.redirect("/")

class Cancel(webapp.RequestHandler):
    def get(self):
        "山行企画の申し込みをキャンセルする。"
        user, rec = getUserAndKey(self)
        if user is None:
            err("invalid user/key")
            return

        if not user in rec.members:
            err("no user")
            return

        # 参加者一覧から、このユーザーを削除する。
        i = rec.members.index(user)
        del rec.members[i]
        rec.put()
        dbgprint("%s canceled for %s" % (user, rec.title))
        self.redirect("/")

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            body = u"<a href='/_ah/login_required'>ログイン</a><br>"
        else:
            body = u'こんにちわ %s さん。<a href="%s">ログアウト</a><br>' % \
                (user.nickname(),
                users.create_logout_url(self.request.uri))

        # 山行企画を表示し、申し込みとキャンセルのリンクをつける。
        query =  db.GqlQuery("""SELECT * FROM Kikaku ORDER BY no DESC""")

        kikakuList = []
        for rec in query:
            moushikomi = ""
            # 自分の申し込みは、取り消せる。
            # 同じ所に２度、申し込みはできない。
            if user and user.nickname() in rec.members:
                moushikomi = u"<a href=/cancel?key=%s>取り消す</a>" % rec.key()

            # 締切日をすぎていれば、申し込みは表示しない。
            #elif rec.shimekiri < datetime.date.today():
            #    moushikomi = ""

            # 定員を超えていれば、おなじく。
            # 定員ゼロは、無限に受付。
            elif rec.teiin != 0 and rec.teiin <= len(rec.members):
                moushikomi = ""
            elif user:
                moushikomi = u"<a href=/apply?key=%s>申し込む</a>" % rec.key()
            
            kikakuList.append(unicode(rec) + " " + moushikomi)

        body += "<br>\n".join(kikakuList)

        template_values = { 'body': body, }

        # ところで、app.yaml に、テンプレートを static と書いてはいけない。
        self.response.headers['Content-Type'] = "text/html; charset=Shift_JIS"
        self.response.out.write(template.render("templates/main.tmpl", template_values))

class InitLoad(webapp.RequestHandler):
    def get(self):
        dbgprint("InitLoad")
        rec = Kikaku(no = 243, title = u"薬師岳、雲の平", rank = "C-C-8.5",
            start = tukihi2Date(u"8月8日"), end = tukihi2Date(u"8月12日"),
            shimekiri = tukihi2Date(u"6月24日"), teiin = 10,
            leaders = [u"大友", u"三浦"])
        rec.put()

        rec = Kikaku(no = 245, title = u"御岳山滝巡り", rank = "A-B-3.5",
            start = tukihi2Date(u"7月1日"), end = tukihi2Date(u"7月1日"),
            shimekiri = tukihi2Date(u"6月28日"), teiin = 0,
            leaders = [u"田辺", u"居関"])
        rec.put()
        self.response.out.write('<html><body>done</body></html>')

class DeleteAll(webapp.RequestHandler):
    def get(self):
        for rec in Kikaku.all():
            db.delete(rec)

        self.response.out.write('<html><body>delete done</body></html>')
            
#        err(self, "not implemented")

application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/apply', Apply),
    ('/cancel', Cancel),
    ('/deleteall', DeleteAll),
    ('/initload', InitLoad)
    ], debug=True)

def main():
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
# eof
