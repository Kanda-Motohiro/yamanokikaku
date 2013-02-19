#!/usr/bin/env python
# encoding=utf-8
# http://yamanokikaku.appspot.com/login.py
# Copyright (c) 2008, 2013 Kanda.Motohiro@gmail.com
# Licensed under the Apache License, Version 2.0

from google.appengine.ext import db
from google.appengine.api import users
import urllib
import tweepy
from util import *
import model
import facebookoauth


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

    # twitter/facebook
    uid = handler.session.get("uid")
    if uid:
        return uid

    return None


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
consumer_key = "63g31tILRVbmELMAbuX2Bg"


class Login(BaseHandler):
    def get(self):
        # twitter ログインの準備
        # thanks to http://pythonhosted.org/tweepy/html/auth_tutorial.html
        consumer_secret = model.configs["twitter_consumer_secret"]
        callback_url = "http://%s/twlogin" % \
            self.request.environ.get("HTTP_HOST")
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
        try:
            tw_redirect_url = auth.get_authorization_url()

            self.session["tw_token"] = (auth.request_token.key,
                                            auth.request_token.secret)

        except tweepy.TweepError, e:
            logerror(e)
            tw_redirect_url = None

        # 以下は OpenID
        body = "<p><a href='%s'>google</a></p>" % \
        users.create_login_url(
            federated_identity='www.google.com/accounts/o8/id') + \
            "<p><a href='%s'>mixi</a></p>" % \
        users.create_login_url(federated_identity='mixi.jp') + \
        "<p><a href='%s'>biglobe</a></p>" % \
        users.create_login_url(federated_identity='openid.biglobe.ne.jp') + \
        "<p><a href='%s'>yahoo</a></p>" % \
        users.create_login_url(federated_identity='yahoo.co.jp')

        if tw_redirect_url:
            body += "<p><a href='%s'>twitter</a></p>" % tw_redirect_url

        # facebook login
        # thanks to facebook-sdk/examples/oauth/facebookoauth.py
        args = dict(client_id=facebookoauth.FACEBOOK_APP_ID,
                    redirect_uri="http://%s/fblogin" % \
                        self.request.environ.get("HTTP_HOST"))
        facebok_login_url = "https://graph.facebook.com/oauth/authorize?" + \
            urllib.urlencode(args)
        body += "<p><a href='%s'>facebook</a></p>" % facebok_login_url

        render_template_and_write_in_sjis(self, 'login.tmpl', body)


class TwLogin(BaseHandler):
    def get(self):
        "twitter でログインした後、リダイレクトされてくるコールバック"
        token = self.session.get("tw_token")
        verifier = self.request.get("oauth_verifier")

        if token and verifier:
            pass
        else:
            msg = "token=%s verifier=%s" % \
                (token, verifier)
            if not verifier:
                # アプリケーション認証を断られました
                logerror(msg)
                self.redirect("/")
            err(self, u"もう一度、ログインしてください。 " + msg)
            # ２回やったら、うまくいったことがあった。
            return

        consumer_secret = model.configs["twitter_consumer_secret"]
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_request_token(token[0], token[1])

        try:
            auth.get_access_token(verifier)
        except tweepy.TweepError, e:
            err(self, e)
            return

        # これはもういらない
        del self.session["tw_token"]

        # ユニークな数字のID みたいなものは、ないのかな。
        name = auth.get_username()
        dbgprint(name)
        self.session["uid"] = name

        self.redirect("/")


def getLogoutUrl(handler):
    if handler.session.get("uid"):
        return "/logout"
    return users.create_logout_url("/")


class Logout(BaseHandler):
    def get(self):
        "oauth のときは、自分でクッキーにログイン状態を持っているので、消す。"
        if self.session.get("uid"):
            del self.session["uid"]
        facebookoauth.fbLogoutHook(self)

        self.redirect("/")
# eof
