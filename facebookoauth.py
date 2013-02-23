#!/usr/bin/env python
# encoding=utf-8
#
# Copyright 2010 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Copyright (c) 2013 Kanda.Motohiro@gmail.com

"""A barebones AppEngine application that uses Facebook for login.

This application uses OAuth 2.0 directly rather than relying on Facebook's
JavaScript SDK for login. It also accesses the Facebook Graph API directly
rather than using the Python SDK. It is designed to illustrate how easy
it is to use the Facebook Platform without any third party code.

See the "appengine" directory for an example using the JavaScript SDK.
Using JavaScript is recommended if it is feasible for your application,
as it handles some complex authentication states that can only be detected
in client-side code.
"""
import base64
import cgi
import Cookie
import email.utils
import hashlib
import hmac
import logging
import os.path
import time
import urllib
import wsgiref.handlers

from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from util import BaseHandler, logerror, dbgprint, err
import model

FACEBOOK_APP_ID = "262276473906025"


class FbLogin(BaseHandler):
    def get(self):
        # http://developers.facebook.com/docs/howtos/login/server-side-login/
        # に、こうせよと書いてあるけど。
        state = self.session.get("fb_state")
        state2 = self.request.get("state")
        if state and state2 and state == state2:
            pass
        else:
            err(self, "state does not match. CSRF?. %s:%s " % (state, state2))
            return

        code = self.request.get("code")
        if not code:
            # 4.1.2.1 error というのが、フォームに入ってくる。
            err(self, "code not found. " + self.request.get("error"))
            return
        # なんで、urlopen するのに、redirect_uri が必要か、と思ったが、
        # そういう、oauth 2.0 仕様なんだそうだ。4.1 (E)
        args = dict(client_id=FACEBOOK_APP_ID,
                    redirect_uri=self.request.path_url,
                    client_secret=model.configs["facebook_app_secret"],
                    code=code)
        try:
            response = cgi.parse_qs(urllib.urlopen(
            "https://graph.facebook.com/oauth/access_token?" +
            urllib.urlencode(args)).read())
        except Exception, e:
            err(self, "access_token " + str(e))
            return
        # json で返ってくるはず。
        if "access_token" not in response:
            err(self, "access_token not found " + str(response))
            return
        access_token = response["access_token"][-1]

        # Download the user profile and cache a local instance of the
        # basic profile info
        try:
            profile = json.load(urllib.urlopen(
            "https://graph.facebook.com/me?" +
            urllib.urlencode(dict(access_token=access_token))))
        except Exception, e:
            err(self, "me " + e)
            return

        name=profile["name"]
        set_cookie(self.response, "fb_user", str(profile["id"]),
                   expires=time.time() + 30 * 86400)

        self.session["uid"] = name
        # これはもういらない。
        del self.session["fb_state"]
        dbgprint("name=%s id=%s logged in with facebook" % (name, profile["id"]))
        self.redirect("/")


def fbLogoutHook(self):
    set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)


def set_cookie(response, name, value, domain=None, path="/", expires=None):
    """Generates and signs a cookie for the give name/value"""
    timestamp = str(int(time.time()))
    value = base64.b64encode(value)
    signature = cookie_signature(value, timestamp)
    cookie = Cookie.BaseCookie()
    cookie[name] = "|".join([value, timestamp, signature])
    cookie[name]["path"] = path
    if domain:
        cookie[name]["domain"] = domain
    if expires:
        cookie[name]["expires"] = email.utils.formatdate(
            expires, localtime=False, usegmt=True)
    response.headers.add("Set-Cookie", cookie.output()[12:])


def parse_cookie(value):
    """Parses and verifies a cookie value from set_cookie"""
    if not value:
        return None
    parts = value.split("|")
    if len(parts) != 3:
        return None
    if cookie_signature(parts[0], parts[1]) != parts[2]:
        logging.warning("Invalid cookie signature %r", value)
        return None
    timestamp = int(parts[1])
    if timestamp < time.time() - 30 * 86400:
        logging.warning("Expired cookie %r", value)
        return None
    try:
        return base64.b64decode(parts[0]).strip()
    except:
        return None


def cookie_signature(*parts):
    """Generates a cookie signature.

    We use the Facebook app secret since it is different for every app (so
    people using this example don't accidentally all use the same secret).
    """
    hash = hmac.new(model.configs["facebook_app_secret"], 
            digestmod=hashlib.sha1)
    for part in parts:
        hash.update(part)
    return hash.hexdigest()
# eof
