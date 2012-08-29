#!/usr/bin/env python
# encoding=utf-8
# do_openid_login.py
# Copyright (c) 2011 Kanda.Motohiro@gmail.com
import os
from util import *
from google.appengine.dist import use_library, _library
try:
    use_library('django', '1.2')
except _library.UnacceptableVersionError, e:
    dbgprint(e)
    pass
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users

from django.template import Context, loader
import settings

# http://code.google.com/intl/ja/appengine/articles/openid.html
# が、サンプルコード。

class OpenIDLoginHandler(webapp.RequestHandler):
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

        self.response.headers['Content-Type'] = "text/html; charset=Shift_JIS"
        t = loader.get_template('blank.tmpl')
        uni = t.render(Context({'body': body}))
        self.response.out.write(uni.encode("Shift_JIS", "replace"))

application = webapp.WSGIApplication([
    ('/_ah/login_required', OpenIDLoginHandler)
    ], debug=True)

def main():
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
# eof
