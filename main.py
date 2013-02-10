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
from google.appengine.ext import db
from google.appengine.api import users
import webapp2
from util import *
#from util import date2Tukihi,shimekiriNashi,date2Tukihi,logerror,err, \
#render_template_and_write_in_sjis,dbgprint,renderKaiinTemplate,
import login
import model


#
# handlers
#
class Apply(webapp2.RequestHandler):
    def get(self):
        "山行企画に申し込む。企画のキーが渡る。"
        rec, user = login.getKikakuAndKaiin(self)
        if isinstance(rec, str):
            err(self, "invalid user/key " + rec)
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

                render_template_and_write_in_sjis(self, 'blank.tmpl', body)
                return

        # 参加者一覧に、このユーザーを追加する。
        rec.members.append(name)
        rec.put()

        # 会員の方にも、この企画を申し込んだことを覚えておく。
        user.kikakuList.append(rec.key())
        user.put()

        rireki = model.MoushikomiRireki(applyCancel="a",
            kaiin=name, kikakuNo=rec.no, kikakuTitle=rec.title)
        rireki.put()
        dbgprint("%s applied for %d %s" % (name, rec.no, rec.title))

        self.redirect("/detail?key=%s" % rec.key())


class Cancel(webapp2.RequestHandler):
    def get(self):
        "山行企画の申し込みをキャンセルする。"
        rec, user = login.getKikakuAndKaiin(self)
        if isinstance(rec, str):
            err(self, "invalid user/key " + rec)
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


class Detail(webapp2.RequestHandler):
    def get(self):
        " 山行企画を表示し、申し込みとキャンセルのリンクをつける。"
        rec, user = login.getKikakuAndKaiin(self)
        if isinstance(rec, str):
            err(self, "invalid user/key " + rec)
            return

        moushikomi = ""
        # 自分の申し込みは、取り消せる。
        # 同じ所に２度、申し込みはできない。
        if user.displayName() in rec.members:
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
        else:
            moushikomi = u"<a href='/apply?key=%s'>申し込む</a>" % rec.key()

        # 応募者一覧を、その山行履歴を見られるリンクで表示する。
        memberLinks = []
        for dname in rec.members:
            no, name = model.parseDisplayName(dname)
            memberLinks.append(u"<a href='/sankourireki?no=%d'>%d</a> %s" %
                (no, no, name))

        body = "No. %d " % rec.no + unicode(rec) + "<br>\n" + \
            u"リーダー：%s " % ",".join(rec.leaders) + \
            u"メンバー：%s " % ",".join(memberLinks) + \
            "<br>\n" + moushikomi + "<br>\n" + \
            u"""<br><a href='/shimekiri?key=%s'>応募者名簿を表示する</a>。
            デモのため、事務局以外の一般会員からも操作できるようにしています。""" % rec.key()

        render_template_and_write_in_sjis(self, 'blank.tmpl', body)
        return


class SankouRireki(webapp2.RequestHandler):
    def get(self):
        "指定された会員の、今までの山行履歴を表示する。"
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

        render_template_and_write_in_sjis(self, 'blank.tmpl', body)
        return


class Shimekiri(webapp2.RequestHandler):
    def get(self):
        """key で指定された山行企画の締切日が来たので、応募者のリストを
        表示する。"""
        rec = login.getKikaku(self)
        if isinstance(rec, str):
            err(self, "invalid key " + rec)
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
        render_template_and_write_in_sjis(self, 'blank.tmpl', body)
        return


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

    query = db.GqlQuery("SELECT * FROM Kikaku WHERE start >= :1 \
                ORDER BY start ASC", start)

    user = users.get_current_user()
    kikakuList = []
    for rec in query:
        if user:
            no = "<a href='/detail?key=%s'>%d</a> " % (rec.key(), rec.no)
        else:
            no = "%d " % rec.no

        if not table:
            kikaku = "No." + no + unicode(rec)
            if user:
                kikaku += rec.leadersMembers()
        else:
            kikaku = u"""<tr>
<td>%s</td><td>%s</td><td>%s</td><td>%s</td>
<td>%s</td><td>%s</td><td>%d</td>
</tr>""" % \
            (no, rec.title, rec.rank, rec.kijitu(),
            rec.shimekiribi(), rec.teiinStr(), len(rec.members))

            if user:
                if len(rec.members) == 0:
                    members = u""
                elif len(rec.members) < 4:
                    members = ",".join(rec.members)
                else:
                    members = ",".join(rec.members[:4]) + "..."

                kikaku += u"<tr><td colspan='7'>\
                    リーダー:%s | メンバー:%s</td></tr>" % \
                    (",".join(rec.leaders), members)

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
        self.response.headers['Content-Type'] = "text/plain"
        self.response.out.write("key=%s" % key)

app = webapp2.WSGIApplication([
    ('/', login.MainPage),
    ('/login', login.Login),
    ('/table', Table),
    ('/detail', Detail),
    ('/shimekiri', Shimekiri),
    ('/kaiin', login.KaiinTouroku),
    ('/unsubscribe', login.KaiinSakujo),
    ('/sankourireki', SankouRireki),
    ('/debug', Debug),
    ('/apply', Apply),
    ('/cancel', Cancel)
    ], debug=True)
#        err(self, "not implemented")
# eof
