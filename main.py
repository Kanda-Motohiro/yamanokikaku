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


class Kikaku(db.Model):
    "山行企画"
    no = db.IntegerProperty(required=True)  # No. 243
    title = db.StringProperty(required=True)  # 薬師岳、雲の平
    rank = db.StringProperty()  # C-C-8.5
    start = db.DateProperty(required=True)  # 8/8
    end = db.DateProperty()  # 8/12
    shimekiri = db.DateProperty(required=True)  # 締切日 6/24
    teiin = db.IntegerProperty()  # 定員　１０人
    leaders = db.StringListProperty()  # リーダー　大友、三浦
    members = db.StringListProperty()

    def __cmp__(self, other):
        # start でソートする
        return cmp(self.start, other.start)

    def leadersMembers(self):
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
        "日本語で示した、開始日と終了日"
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


class Kaiin(db.Model):
    """山岳会の会員
    会員名簿は、持ちたくなかったが、リーダーに参加者の
    緊急連絡先を伝える必要があるから、しかたないか。
    OpenID が携帯電話から使えないようなので、
    携帯端末の識別番号でログインさせることになるかも。
    """
    no = db.IntegerProperty(required=True)  # 会員番号 9000
    name = db.StringProperty(required=True)  # 田部井淳子
    openid = db.StringProperty()  # user.nickname

    seibetsu = db.StringProperty()  # 女
    tel = db.PhoneNumberProperty()  # 046-123-4567
    fax = db.PhoneNumberProperty()
    mail = db.EmailProperty()  # junko-tabei@gmail.com
    address = db.PostalAddressProperty()

    # 緊急連絡先
    kinkyuName = db.StringProperty()
    kinkyuKankei = db.StringProperty()  # 夫
    kinkyuAddress = db.PostalAddressProperty()
    kinkyuTel = db.PhoneNumberProperty()

    # 最近行った山
    saikin0 = db.StringProperty()  # 鳳凰三山　２０１２年８月
    saikin1 = db.StringProperty()
    saikin2 = db.StringProperty()

    kanyuuHoken = db.StringProperty()  # 山岳保険、ハイキング保険

    # 申し込んだ山行企画
    kikakuList = db.ListProperty(db.Key)

    def displayName(self):
        "番号と氏名を、組でよく使う。"
        return u"%d %s" % (self.no, self.name)

    def __repr__(self):
        return u"""no=%d %s %s 電話=%s fax=%s メール=%s 住所=%s
        緊急連絡先 %s %s %s %s  最近行った山 %s %s %s %s
        """ % (self.no, self.name, self.seibetsu,
        self.tel, self.fax, self.mail, self.address,
        self.kinkyuName, self.kinkyuKankei, self.kinkyuAddress,
        self.kinkyuTel,
        self.saikin0, self.saikin1, self.saikin2,
        self.kanyuuHoken)

    def updateFromDict(self, f):
        # なんか、自動的にやる方法ないんだっけ
        if "seibetsu" in f:
            self.seibetsu = f["seibetsu"]
        if "tel" in f:
            self.tel = f["tel"]
        if "fax" in f:
            self.fax = f["fax"]
        if "mail" in f:
            self.mail = f["mail"]
        if "address" in f:
            self.address = f["address"]
        if "kinkyuName" in f:
            self.kinkyuName = f["kinkyuName"]
        if "kinkyuKankei" in f:
            self.kinkyuKankei = f["kinkyuKankei"]
        if "kinkyuAddress" in f:
            self.kinkyuAddress = f["kinkyuAddress"]
        if "kinkyuTel" in f:
            self.kinkyuTel = f["kinkyuTel"]
        if "saikin0" in f:
            self.saikin0 = f["saikin0"]
        if "saikin1" in f:
            self.saikin1 = f["saikin1"]
        if "saikin2" in f:
            self.saikin2 = f["saikin2"]
        if "kanyuuHoken" in f:
            self.kanyuuHoken = f["kanyuuHoken"]

blankKaiin = Kaiin(no=0, name=u"未登録")


def parseDisplayName(dname):
    els = dname.split()
    if len(els) != 2:
        return 0, els[0]
    return int(els[0]), els[1]


class MoushikomiRireki(db.Model):
    "申し込みの履歴。いつ、誰が、何に応募したか。"
    created = db.DateTimeProperty(auto_now_add=True)
    applyCancel = db.StringProperty()  # "apply"/"cancel"

    kaiin = db.StringProperty()

    kikakuNo = db.IntegerProperty()
    kikakuTitle = db.StringProperty()

# end class


def openid2Kaiin(openid):
    "OpenID ニックネームをもらい、会員レコードを返す。"
    query = db.GqlQuery("SELECT * FROM Kaiin WHERE openid = :1", openid)
    recs = query.fetch(1)
    if recs:
        return recs[0]
    else:
        return None


def getKikaku(handler):
    "山行企画のキーをもらって、データベースレコードを返す。"
    key = handler.request.get('key')
    if not key:
        logerror("no key")
        return "no key"

    try:
        rec = db.get(key)
    except db.BadKeyError:
        logerror("bad key", key)
        return "bad key"

    if rec is None:
        logerror("no record", key)
        return "no record"

    return rec


def getKaiin():
    user = users.get_current_user()
    if not user:
        logerror("no user")
        return "no user"

    kaiin = openid2Kaiin(user.nickname())
    if not kaiin:
        logerror("not kaiin")
        return "not kaiin"

    return kaiin


def getKikakuAndKaiin(handler):
    """申し込みとキャンセルで使われる、企画と会員レコードを返す。
    エラーがいろいろあるので、最初の戻り値に文字列で返す。
    基本的に、これらは、バグ。
    """
    kikaku = getKikaku(handler)
    if isinstance(kikaku, str):
        return kikaku, None

    kaiin = getKaiin()
    if isinstance(kaiin, str):
        return kaiin, None

    return kikaku, kaiin


#
# handlers
#
class Apply(webapp2.RequestHandler):
    def get(self):
        "山行企画に申し込む。企画のキーが渡る。"
        rec, user = getKikakuAndKaiin(self)
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

        rireki = MoushikomiRireki(applyCancel="a",
            kaiin=name, kikakuNo=rec.no, kikakuTitle=rec.title)
        rireki.put()
        dbgprint("%s applied for %d %s" % (name, rec.no, rec.title))

        self.redirect("/detail?key=%s" % rec.key())


class Cancel(webapp2.RequestHandler):
    def get(self):
        "山行企画の申し込みをキャンセルする。"
        rec, user = getKikakuAndKaiin(self)
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

        rireki = MoushikomiRireki(applyCancel="c",
            kaiin=name, kikakuNo=rec.no, kikakuTitle=rec.title)
        rireki.put()
        dbgprint("%s canceled for %d %s" % (name, rec.no, rec.title))

        self.redirect("/detail?key=%s" % rec.key())


class Detail(webapp2.RequestHandler):
    def get(self):
        " 山行企画を表示し、申し込みとキャンセルのリンクをつける。"
        rec, user = getKikakuAndKaiin(self)
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
            no, name = parseDisplayName(dname)
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
        rec = getKikaku(self)
        if isinstance(rec, str):
            err(self, "invalid key " + rec)
            return

        body = "No. %d " % rec.no + unicode(rec) + "<br>\n" + \
            u"リーダー：" + ",".join(rec.leaders) + "<hr>"

        kaiinList = []
        # すべての応募者の、緊急連絡先を含む、応募者名簿を表示する。
        for dname in rec.members:
            no, _ = parseDisplayName(dname)

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


def parseKaiinForm(request):
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

    out["name"] = name
    out["no"] = no

    for key in ("seibetsu", "tel", "fax", "mail", "address",
        "kinkyuName", "kinkyuKankei", "kinkyuAddress", "kinkyuTel",
        "saikin0", "saikin1", "saikin2", "kanyuuHoken"):
        val = request.get(key)
        if val != "":
            out[key] = val

    return out, ""


class KaiinTouroku(webapp2.RequestHandler):
    def get(self):
        """山岳会の会員番号、氏名と、openid の対応をもらう。
        緊急連絡先なども、入れてもらう。
        """
        kaiin = getKaiin()
        # 新規登録か、更新か。
        if isinstance(kaiin, str):
            kaiin = blankKaiin

        body = users.create_logout_url("/")

        renderKaiinTemplate(self, body, kaiin)

    def post(self):
        f, error = parseKaiinForm(self.request)
        if f is None:
            render_template_and_write_in_sjis(self, 'blank.tmpl', error)
            return

        user = users.get_current_user()
        if not user:
            err(self, "no user at post")
            return

        # 管理者は、任意の会員情報を生成、変更できる。
        if 0:  # XXX これだと、main で、自分が誰か探せない。users.is_current_user_admin():
            openid = None
            query = db.GqlQuery("SELECT * FROM Kaiin WHERE no = :1", f["no"])
        else:
            openid = user.nickname()

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
            rec = Kaiin(no=f["no"], name=f["name"], openid=openid)
            dbgprint("new kaiin no %d name %s" % (f["no"], f["name"]))

        rec.updateFromDict(f)
        rec.put()
        self.redirect("/")


class KaiinSakujo(webapp2.RequestHandler):
    def get(self):
        "自分の登録情報を忘れさせる。"
        kaiin = getKaiin()
        if isinstance(kaiin, str):
            err(self, "cannot delete kaiin " + kaiin)
            return
        db.delete(kaiin)
        self.redirect("/")


class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            body = u"""申し込みなどをするには、
            <a href='/login'>ログイン</a>して、会員登録をして下さい。"""
        else:
            kaiin = openid2Kaiin(user.nickname())
            if not kaiin:
                # ログインしたけど、会員データベースにないときは、登録画面へ
                self.redirect("/kaiin")
                return
            else:
                body = u"""こんにちわ %s さん。申し込み、取り消しをするには、
番号をクリックして下さい。<br>
<a href='/kaiin'>会員情報</a>&nbsp;
<a href='/sankourireki?no=%d'>最近行った山</a>&nbsp;
<a href='%s'>ログアウト</a>。""" % \
                (kaiin.displayName(), kaiin.no,
                    users.create_logout_url(self.request.uri))

        # 山行企画一覧を表示する。会員には、申し込みもできる詳細ページの
        # リンクを示す。

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


class Login(webapp2.RequestHandler):
    def get(self):
        body = "<p><a href='%s'>google</a></p>" % \
        users.create_login_url(
            federated_identity='www.google.com/accounts/o8/id') + \
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

        recs = db.GqlQuery("SELECT * FROM Kikaku").fetch(1)
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
    ('/shimekiri', Shimekiri),
    ('/kaiin', KaiinTouroku),
    ('/unsubscribe', KaiinSakujo),
    ('/sankourireki', SankouRireki),
    ('/debug', Debug),
    ('/apply', Apply),
    ('/cancel', Cancel)
    ], debug=True)
#        err(self, "not implemented")
# eof
