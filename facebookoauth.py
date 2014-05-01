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
import cgi
import urllib
from django.utils import simplejson as json
from util import dbgprint, err
import model
import session

FACEBOOK_APP_ID = "262276473906025"


class FbLogin(session.BaseHandler):
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

        name = profile["name"]
        id = profile["id"]

        # 数字の id, 発行元も含めて、ユニークにする。
        self.session["uid"] = name + "." + id + "@facebook"

        # これはもういらない。
        del self.session["fb_state"]
        dbgprint("name=%s id=%s logged in with facebook" % (name, id))
        self.redirect("/")

# eof
