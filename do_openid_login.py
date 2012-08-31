#!/usr/bin/env python
# encoding=utf-8
# do_openid_login.py
# Copyright (c) 2011 Kanda.Motohiro@gmail.com
import os
from util import *
import wsgiref.handlers
from google.appengine.api import users
import webapp2
import settings

# http://code.google.com/intl/ja/appengine/articles/openid.html
# が、サンプルコード。

class OpenIDLoginHandler(webapp2.RequestHandler):
    def get(self):
        dbgprint(settings.TEMPLATE_DIRS)
        user = users.get_current_user()
        if user:
            body = u'<a href="%s">ログアウト</a>' % \
                users.create_logout_url(self.request.uri)
        else:
            body = u"お持ちのID でログインください。<br>" + \
            "<p><a href='%s'>google</a></p>" % \
            users.create_login_url(federated_identity='www.google.com/accounts/o8/id') + \
            "<p><a href='%s'>mixi</a></p>" % \
            users.create_login_url(federated_identity='mixi.jp') + \
            "<p><a href='%s'>biglobe</a></p>" % \
            users.create_login_url(federated_identity='openid.biglobe.ne.jp') + \
            "<p><a href='%s'>yahoo</a></p>" % \
            users.create_login_url(federated_identity='yahoo.co.jp')

        render_template_and_write_in_sjis(self, 'blank.tmpl', body)

app = webapp2.WSGIApplication([
    ('/_ah/login_required', OpenIDLoginHandler)
    ], debug=True)
# eof
