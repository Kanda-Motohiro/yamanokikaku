#!/usr/bin/env python
# encoding=utf-8
# http://yamanokikaku.appspot.com/main.py
# Copyright (c) 2008, 2012 Kanda.Motohiro@gmail.com
# Licensed under the Apache License, Version 2.0

"""todo
確認のメールを発信。
バックアップ。
事務局による、FAX からの転載による応募
しめきり処理。参加者名簿を印刷、リーダーにメール送信。
"""
import datetime
import cgi
import hashlib
import random
from google.appengine.ext import db
import webapp2
from util import *
#from util import date2Tukihi,shimekiriNashi,date2Tukihi,logerror,err, \
#render_template_and_write_in_sjis,dbgprint,renderKaiinTemplate,
import model
import login
from login import getKikakuAndKaiin, getKikaku, getCurrentUserId, \
getKaiin, openid2Kaiin, getLogoutUrl
import facebookoauth

# oauth サポートのため、クッキーでセッション管理をする。以下のサンプル参照。
# http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
a = hashlib.md5(model.configs["twitter_consumer_secret"] +
    model.configs["facebook_app_secret"])
config = {"webapp2_extras.sessions":
{ "secret_key": a.hexdigest(),
"cookie_args": {"secure":False, "httponly":True} }}


#
# handlers
#
class Apply(BaseHandler):
    def get(self):
        "山行企画に申し込む。key= で、企画のキーが与えられる。"
        rec, user = getKikakuAndKaiin(self)
        if rec is None:
            err(self, "invalid user/key")
            return

        name = user.displayName()
        if name in rec.members:
            err(self, "dup user")
            return

        # この会員が、現在申し込んでいるものと、期日が重複してはいけない。
        for key in user.kikakuList:
            other = db.get(key)
            if other.start <= rec.start <= other.end or \
                other.start <= rec.end <= other.end:

                body = u"""既にお申し込みの、%d %s %s と、期日が重複しています。
%d %s %s のお申し込みはできません。""" % \
                (other.no, other.title, other.kijitu(),
                rec.no, rec.title, rec.kijitu())

                render_template_and_write_in_sjis(self, "blank.tmpl", body)
                return

        # 参加者一覧に、このユーザーを追加する。
        rec.members.append(name)
        rec.put()

        # 会員の方にも、この企画を申し込んだことを覚えておく。
        user.kikakuList.append(rec.key())
        user.put()

        # 申し込み、キャンセルの履歴を覚えておく。
        rireki = model.MoushikomiRireki(applyCancel="a",
            kaiin=name, kikakuNo=rec.no, kikakuTitle=rec.title)
        rireki.put()
        dbgprint("%s applied for %d %s" % (name, rec.no, rec.title))

        self.redirect("/detail?key=%s" % rec.key())


class Cancel(BaseHandler):
    def get(self):
        "山行企画の申し込みをキャンセルする。"
        rec, user = getKikakuAndKaiin(self)
        if rec is None:
            err(self, "invalid user/key ")
            return

        name = user.displayName()

        if not name in rec.members:
            err(self, "no user")
            return

        # 参加者一覧から、このユーザーを削除する。
        i = rec.members.index(name)
        del rec.members[i]
        rec.put()

        # 会員の方も、取り消し
        i = user.kikakuList.index(rec.key())
        del user.kikakuList[i]
        user.put()

        rireki = model.MoushikomiRireki(applyCancel="c",
            kaiin=name, kikakuNo=rec.no, kikakuTitle=rec.title)
        rireki.put()
        dbgprint("%s canceled for %d %s" % (name, rec.no, rec.title))

        self.redirect("/detail?key=%s" % rec.key())


class Detail(BaseHandler):
    def get(self):
        """key= で与えられた、１つの山行企画を表示し、
        申し込みとキャンセルのリンクをつける。"""
        rec, user = getKikakuAndKaiin(self)
        if rec is None:
            err(self, "invalid user/key")
            return

        moushikomi = ""
        # 自分の申し込みは、取り消せる。
        # 同じ所に２度、申し込みはできない。
        if user.displayName() in rec.members:
            moushikomi = u'<a href="/cancel?key=%s">取り消す</a>' % rec.key()

        # 締切日をすぎていれば、申し込みは表示しない。
        #elif rec.shimekiri < datetime.date.today():
        # デモなので、この日付とする。
        elif rec.shimekiri < datetime.date(2012, 8, 10):
            moushikomi = u"""申し込みは締めきりました。<br>
デモのため、現在日付を、８月１０日にしています。これより前の締切日の企画は、
申し込みをできなくしてあります。"""

        # 定員を超えていれば、おなじく。
        # 定員ゼロは、無限に受付。
        #elif rec.teiin != 0 and rec.teiin <= len(rec.members):
        #    moushikomi = ""
        # なのだけど、定員以上を受け付けることもあるので、この制限はやめ。
        else:
            moushikomi = u'<a href="/apply?key=%s">申し込む</a>' % rec.key()

        # 応募者一覧を、その山行履歴を見られるリンクつきで表示する。
        memberLinks = []
        for dname in rec.members:
            no, name = model.parseDisplayName(dname)
            memberLinks.append(u'<a href="/sankourireki?no=%d">%d</a> %s' %
                (no, no, name))

        body = "No. %d " % rec.no + unicode(rec) + "<br>\n" + \
            u"リーダー：%s " % ",".join(rec.leaders) + \
            u"メンバー：%s " % ",".join(memberLinks) + \
            "<br>\n" + moushikomi + "<br>\n" + \
            u"""<br><a href="/shimekiri?key=%s">応募者名簿を表示する</a>。
            デモのため、事務局以外の一般会員からも操作できるようにしています。""" % rec.key()

        render_template_and_write_in_sjis(self, "blank.tmpl", body)
        return


class SankouRireki(webapp2.RequestHandler):
    def get(self):
        """no= で指定された会員の、今までの山行履歴を表示する。
        自分、ではない。会員は、他の任意の会員の履歴を参照できる。
        """
        key = self.request.get("no")
        if not key:
            err(self, "no")
            return
        try:
            no = int(key)
        except ValueError:
            err(self, "no=%s" % key)
            return

        query = db.GqlQuery("SELECT * FROM Kaiin WHERE no = :1", no)
        recs = query.fetch(1)
        if not recs:
            err(self, "no kaiin rec=%s" % key)
            return
        kaiin = recs[0]

        rireki = []
        for key in kaiin.kikakuList:
            kikaku = db.get(key)
            rireki.append(kikaku)

        # 古い順に表示したい。ソート順は、class に定義してある。
        rireki.sort()
        text = []
        for kikaku in rireki:
            text.append("%s %d %s" % (date2Tukihi(kikaku.start),
                kikaku.no, kikaku.title))

        body = u"<h2>%s さんの山行履歴</h2>%s<br>" % \
            (kaiin.displayName(), "<br>\n".join(text))

        render_template_and_write_in_sjis(self, "blank.tmpl", body)
        return


class Shimekiri(webapp2.RequestHandler):
    def get(self):
        """key で指定された山行企画の締切日が来たので、応募者のリストを
        表示する。"""
        rec = getKikaku(self)
        if rec is None:
            err(self, "invalid key")
            return

        body = "No. %d " % rec.no + unicode(rec) + "<br>\n" + \
            u"リーダー：" + ",".join(rec.leaders) + "<hr>"

        kaiinList = []
        # すべての応募者の、緊急連絡先を含む、応募者名簿を表示する。
        for dname in rec.members:
            no, _ = model.parseDisplayName(dname)

            query = db.GqlQuery("SELECT * FROM Kaiin WHERE no = :1", no)
            recs = query.fetch(1)
            if not recs:
                dbgprint("invalid dname=%s" % dname)
                continue
            k = recs[0]

            kaiinInfo = u"%d %s %s<br>" % (k.no, k.name, k.seibetsu) + \
            u"電話 %s ＦＡＸ %s<br>メール %s<br>住所 %s<br>" % \
            (k.tel, k.fax, k.mail, k.address) + \
            u"緊急連絡先<br>氏名 %s 本人との関係 %s<br>住所 %s<br>電話 %s" % \
            (k.kinkyuName, k.kinkyuKankei, k.kinkyuAddress, k.kinkyuTel) + \
            "<hr>"

            kaiinList.append(kaiinInfo)

        body += "<br>\n".join(kaiinList)
        render_template_and_write_in_sjis(self, "blank.tmpl", body)
        return


def parseKaiinForm(request):
    "会員登録のフォームをパースして、辞書を返す。"
    out = dict()

    # 氏名はシフトJIS で来るはず
    request.charset = "cp932"
    try:
        # ここで文字コード変換するので、
        name = request.get("name")
    except UnicodeDecodeError, e:
        # いちおう、これも試してみよう
        request.charset = "utf8"
        try:
            name = request.get("name")
        except UnicodeDecodeError, e:
            return None, "%s" % (e)

    no = request.get("no")
    if no != "":
        try:
            no = int(no)
        except ValueError, e:
            no = ""

    if name == "" or no == "":
        error = u"""会員番号（半角数字）とご氏名を入力下さい。<br>
            <a href="/kaiin">入力しなおす</a>。<br>
            """
        return None, error

    out["name"] = cgi.escape(name, quote=True)
    out["no"] = no

    for key in ("seibetsu", "tel", "fax", "mail", "address",
        "kinkyuName", "kinkyuKankei", "kinkyuAddress", "kinkyuTel",
        "saikin0", "saikin1", "saikin2", "kanyuuHoken"):
        val = request.get(key)
        if val != "":
            out[key] = cgi.escape(val, quote=True)

    return out, ""


class KaiinTouroku(BaseHandler):
    def get(self):
        """山岳会の会員番号、氏名と、openid の対応をもらう。
        緊急連絡先なども、入れてもらう。
        """
        kaiin = getKaiin(self)
        # 新規登録か、更新か。
        if kaiin is None:
            kaiin = model.blankKaiin

        body = getLogoutUrl(self)

        renderKaiinTemplate(self, body, kaiin)

    def post(self):
        f, error = parseKaiinForm(self.request)
        if f is None:
            render_template_and_write_in_sjis(self, "blank.tmpl", error)
            return

        uid = getCurrentUserId(self)
        if uid is None:
            err(self, "no user at post")
            return

        # 管理者は、任意の会員情報を生成、変更できる。
        if 0:  # XXX これだと、main で、自分が誰か探せない。users.is_current_user_admin():
            openid = None
            query = db.GqlQuery("SELECT * FROM Kaiin WHERE no = :1", f["no"])
        else:
            openid = uid

        # 会員でない人が、openid アカウントで登録してきたらどうするか。
        # 手元には、有効な会員と氏名の一覧を持たないので、受け入れるしか無い。
        # 少なくとも、１つのアカウントで、１つの会員レコードしか作っては
        # いけない
        # 自分の名前を間違えたので、入れなおし、は拒んではいけない。

            query = db.GqlQuery("SELECT * FROM Kaiin WHERE openid = :1",
                openid)
        # if admin
        recs = query.fetch(1)

        # あれば、更新。なければ、作成。
        if recs:
            rec = recs[0]
            dbgprint("changed no %d->%d name %s->%s" % (rec.no, f["no"],
                rec.name, f["name"]))
            rec.no = f["no"]
            rec.name = f["name"]
        else:
            rec = model.Kaiin(no=f["no"], name=f["name"], openid=openid)
            dbgprint("new kaiin no %d name %s" % (f["no"], f["name"]))

        rec.updateFromDict(f)
        rec.put()
        self.redirect("/")


class KaiinSakujo(BaseHandler):
    def get(self):
        "自分の登録情報を忘れさせる。"
        kaiin = getKaiin(self)
        if kaiin is None:
            err(self, "cannot delete kaiin")
            return
        db.delete(kaiin)
        # 山行企画の方に残っている参加履歴などはそのままでいいかな。
        self.redirect("/")


class MainPage(BaseHandler):
    def get(self):
        " トップページ。ログインへのリンクと、山行一覧。"

        # しばらく、ログイン済みか、会員登録済みか、の判定。
        kaiin = None
        uid = getCurrentUserId(self)
        if uid is None:
            body = u"""申し込みなどをするには、
            <a href="/login">ログイン</a>して、会員登録をして下さい。"""
        else:
            kaiin = openid2Kaiin(uid)
            if kaiin is None:
                # ログインしたけど、会員データベースにないときは、登録画面へ
                self.redirect("/kaiin")
                return
            else:
                body = u"""こんにちわ %s さん。申し込み、取り消しをするには、
番号をクリックして下さい。<br>
<a href="/kaiin">会員情報</a>&nbsp;
<a href="/sankourireki?no=%d">最近行った山</a>&nbsp;
<a href="%s">ログアウト</a>。""" % \
                (kaiin.displayName(), kaiin.no,
                    getLogoutUrl(self))

        # 山行企画一覧を表示する。会員には、申し込みもできる詳細ページの
        # リンクを示す。

        body += SankouKikakuIchiran(kaiin)

        render_template_and_write_in_sjis(self, "main.tmpl", body)
        return

# end MainPage


def SankouKikakuIchiran(kaiin, table=False):
    """山行企画の一覧を、ユニコードの HTML で返す。
    table=True のときは、テーブルタグを使う。
    会員には、参加者名簿や、申し込みリンクを示す。
    """
    # 今月以降の企画を表示する。
    y = datetime.date.today().year
    m = datetime.date.today().month
    start = datetime.date(y, m, 1)
    # だけど、デモなので、しばらくはこうする。
    start = datetime.date(2012, 6, 1)

    query = db.GqlQuery("SELECT * FROM Kikaku WHERE start >= :1 \
                ORDER BY start ASC", start)

    kikakuList = []
    for rec in query:
        if kaiin:
            no = '<a href="/detail?key=%s">%d</a> ' % (rec.key(), rec.no)
        else:
            no = "%d " % rec.no

        if not table:
            kikaku = "No." + no + unicode(rec)
            if kaiin:
                kikaku += rec.leadersMembers()
        else:
            kikaku = u"""<tr>
<td>%s</td><td>%s</td><td>%s</td><td>%s</td>
<td>%s</td><td>%s</td><td>%d</td>
</tr>""" % \
            (no, rec.title, rec.rank, rec.kijitu(),
            rec.shimekiribi(), rec.teiinStr(), len(rec.members))

            if kaiin:
                if len(rec.members) == 0:
                    members = u""
                elif len(rec.members) < 4:
                    members = ",".join(rec.members)
                else:
                    members = ",".join(rec.members[:4]) + "..."

                kikaku += u'<tr><td colspan="7">\
                    リーダー:%s | メンバー:%s</td></tr>' % \
                    (",".join(rec.leaders), members)

        kikakuList.append(kikaku)

    if not table:
        return u"<h2>山行案内一覧</h2>" + "<br>\n".join(kikakuList)
    else:
        return u"<h2>山行案内一覧</h2>" + "<table border=1>" + \
        u"""<tr><th>番号</th><th>名称</th><th>ランク</th><th>期日</th>
<th>締め切り</th><th>定員</th><th>現在</th></tr>""" + \
        "\n".join(kikakuList) + "</table>"


class Table(BaseHandler):
    def get(self):
        "テーブル形式で、山行企画一覧を表示する。"
        kaiin = getKaiin(self)
        body = SankouKikakuIchiran(kaiin, table=True)
        render_template_and_write_in_sjis(self, "blank.tmpl", body)
        return


class Debug(webapp2.RequestHandler):
    def get(self):
        "デバッグ用に、最初の企画レコードのキーを返す。"
        if self.request.environ.get("SERVER_NAME") != "localhost":
            self.error(404)

        recs = db.GqlQuery("SELECT * FROM Kikaku").fetch(1)
        if len(recs) == 0:
            key = "None"
        else:
            key = recs[0].key()
        # プレーンテキスト
        self.response.headers["Content-Type"] = "text/plain"
        self.response.out.write("key=%s" % key)

app = webapp2.WSGIApplication([
    ("/", MainPage),
    ("/login", login.Login),
    ("/pretwlogin", login.PreTwLogin),
    ("/prefblogin", login.PreFbLogin),
    ("/twlogin", login.TwLogin),
    ("/fblogin", facebookoauth.FbLogin),
    ("/logout", login.Logout),
    ("/table", Table),
    ("/detail", Detail),
    ("/shimekiri", Shimekiri),
    ("/kaiin", KaiinTouroku),
    ("/unsubscribe", KaiinSakujo),
    ("/sankourireki", SankouRireki),
    ("/debug", Debug),
    ("/apply", Apply),
    ("/cancel", Cancel)
    ],
    config=config,
    debug=True)
#        err(self, "not implemented")
# eof
