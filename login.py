#!/usr/bin/env python
# encoding=utf-8
# http://yamanokikaku.appspot.com/login.py
# Copyright (c) 2008, 2013 Kanda.Motohiro@gmail.com
# Licensed under the Apache License, Version 2.0

from google.appengine.ext import db
from google.appengine.api import users
import webapp2
import facebook
from util import *
from model import Kaiin, blankKaiin
import main
import facebookexample


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
        return None

    try:
        rec = db.get(key)
    except db.BadKeyError:
        logerror("bad key", key)
        return None

    if rec is None:
        logerror("no record", key)
        return None

    return rec


def getCurrentUserId(handler):
    "グーグルアカウント、OpenID, facebook の id を文字列で返す。"
    user = users.get_current_user()
    if user:
        return user.nickname()

    # base handler で定義される、プロパティ
    user = handler.current_user
    if user is None or "id" not in user:
        return None

    return user["id"]

def getKaiin(handler):
    uid = getCurrentUserId(handler)
    if uid is None:
        logerror("no user")
        return None

    kaiin = openid2Kaiin(uid)
    if not kaiin:
        logerror("not kaiin")
        return None

    return kaiin


def getKikakuAndKaiin(handler):
    """申し込みとキャンセルで使われる、企画と会員レコードを返す。
    """
    kikaku = getKikaku(handler)
    if kikaku is None:
        return None, None

    kaiin = getKaiin(handler)
    if kaiin is None:
        return None, None

    return kikaku, kaiin


#
# handlers
#
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


class KaiinTouroku(facebookexample.BaseHandler):
    def get(self):
        """山岳会の会員番号、氏名と、openid の対応をもらう。
        緊急連絡先なども、入れてもらう。
        """
        kaiin = getKaiin(self)
        # 新規登録か、更新か。
        if kaiin is None:
            kaiin = blankKaiin

        body = "/logout"

        renderKaiinTemplate(self, body, kaiin)

    def post(self):
        f, error = parseKaiinForm(self.request)
        if f is None:
            render_template_and_write_in_sjis(self, 'blank.tmpl', error)
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
            rec = Kaiin(no=f["no"], name=f["name"], openid=openid)
            dbgprint("new kaiin no %d name %s" % (f["no"], f["name"]))

        rec.updateFromDict(f)
        rec.put()
        self.redirect("/")


class KaiinSakujo(facebookexample.BaseHandler):
    def get(self):
        "自分の登録情報を忘れさせる。"
        kaiin = getKaiin(self)
        if kaiin is None:
            err(self, "cannot delete kaiin")
            return
        db.delete(kaiin)
        self.redirect("/")


class MainPage(facebookexample.BaseHandler):
    def get(self):
        kaiin = None
        uid = getCurrentUserId(self)
        if uid is None:
            body = u"""申し込みなどをするには、
            <a href='/login'>ログイン</a>して、会員登録をして下さい。"""
        else:
            kaiin = openid2Kaiin(uid)
            if kaiin is None:
                # ログインしたけど、会員データベースにないときは、登録画面へ
                self.redirect("/kaiin")
                return
            else:
                body = u"""こんにちわ %s さん。申し込み、取り消しをするには、
番号をクリックして下さい。<br>
<a href='/kaiin'>会員情報</a>&nbsp;
<a href='/sankourireki?no=%d'>最近行った山</a>&nbsp;
<a href='/logout'>ログアウト</a>。""" % \
                (kaiin.displayName(), kaiin.no)

        # 山行企画一覧を表示する。会員には、申し込みもできる詳細ページの
        # リンクを示す。

        body += main.SankouKikakuIchiran(kaiin)

        render_template_and_write_in_sjis(self, 'main.tmpl', body)
        return

# end MainPage


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


class Logout(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is None:
            self.redirect("/fblogout")
            return
        body = users.create_logout_url("/")
        render_template_and_write_in_sjis(self, 'logout.tmpl', body)

class FbLogout(webapp2.RequestHandler):
    def get(self):
        render_template_and_write_in_sjis(self, 'fblogout.tmpl',
            facebookexample.FACEBOOK_APP_ID)
# eof