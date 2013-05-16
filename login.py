#!/usr/bin/env python
# encoding=utf-8
# http://yamanokikaku.appspot.com/login.py
# Copyright (c) 2008, 2013 Kanda.Motohiro@gmail.com
# Licensed under the Apache License, Version 2.0

from google.appengine.ext import db
from google.appengine.api import users
import urllib
import hashlib
import random
import hmac
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
    key = handler.request.get("key")
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
    """グーグルアカウント、OpenID, facebook, twitter の id を
    文字列で返す。ユニークになるように、発行元もつける。
    """
    user = users.get_current_user()
    if user:
        # openid の場合、nickname に、https://id.mixi.jp/ などが
        # ついてくるので、federated_provider を使う必要なく、
        # プロバイダーごとにユニークになる。
        return user.nickname()

    # twitter/facebook
    # セッションに入れるときに、@facebook などの文字をつけて、
    # ユニークにしている。
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


class PreTwLogin(BaseHandler):
    def get(self):
        " twitter ログインの準備 "
        # http://pythonhosted.org/tweepy/html/auth_tutorial.html 参照。
        if self.request.environ.get("SERVER_NAME") == "localhost":
            proto = "http"
        else:
            proto = "https"

        consumer_secret = model.configs["twitter_consumer_secret"]
        callback_url = "%s://%s/twlogin" % \
            (proto, self.request.environ.get("HTTP_HOST"))
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
        try:
            tw_redirect_url = auth.get_authorization_url()

            self.session["tw_token"] = (auth.request_token.key,
                                            auth.request_token.secret)

        except tweepy.TweepError, e:
            err(e)
            return
        self.redirect(tw_redirect_url)


class PreFbLogin(BaseHandler):
    def get(self):
        " prepare facebook login "
        # facebook-sdk/examples/oauth/facebookoauth.py 参照。
        # state をセッションに入れて比較するのは、ここ。本当に効果あるの？
        # http://developers.facebook.com/docs/howtos/login/server-side-login/
        if self.request.environ.get("SERVER_NAME") == "localhost":
            proto = "http"
        else:
            proto = "https"

        hash = hmac.new(str(random.random()), digestmod=hashlib.sha1)
        self.session["fb_state"] = hash.hexdigest()
        args = dict(client_id=facebookoauth.FACEBOOK_APP_ID,
                    state=hash.hexdigest(),
                    redirect_uri="%s://%s/fblogin" % \
                        (proto, self.request.environ.get("HTTP_HOST")))

        facebok_login_url = "https://graph.facebook.com/oauth/authorize?" + \
            urllib.urlencode(args)
        self.redirect(facebok_login_url)


class Login(BaseHandler):
    def get(self):
        #
        # OpenID, OAuth
        #
        body = '<p><a href="%s">google</a></p>' % \
        users.create_login_url(
            federated_identity="www.google.com/accounts/o8/id") + \
            '<p><a href="%s">mixi</a></p>' % \
        users.create_login_url(federated_identity="mixi.jp") + \
        '<p><a href="%s">biglobe</a></p>' % \
        users.create_login_url(federated_identity="openid.biglobe.ne.jp") + \
        '<p><a href="%s">yahoo</a></p>' % \
        users.create_login_url(federated_identity="yahoo.co.jp") + \
        '<p><a href="/pretwlogin">twitter</a></p>' + \
        '<p><a href="/prefblogin">facebook</a></p>'

        render_template_and_write_in_sjis(self, "login.tmpl", body)


class TwLogin(BaseHandler):
    def get(self):
        "twitter でログインした後、リダイレクトされてくるコールバック"
        token = self.session.get("tw_token")
        verifier = self.request.get("oauth_verifier")
        error = self.request.get("denied")

        if token and verifier:
            pass
        else:
            msg = "token=%s verifier=%s error=%s" % \
                (token, verifier, error)
            if not verifier:
                # アプリケーション認証を断られました
                logerror(msg)
                self.redirect("/")
                return
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

        api = tweepy.API(auth)
        me = api.me()
        # これで、 id の文字列がとれるらしい。
        nameid = me.screen_name + "." + me.id_str
        self.session["uid"] = nameid + "@twitter"

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

        self.redirect("/")
# eof
