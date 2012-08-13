#!/usr/bin/env python
# encoding=utf-8
# do_openid_login.py
# Copyright (c) 2011 Kanda.Motohiro@gmail.com
import os
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users

webapp.template.register_template_library('sjisfilter')

# http://code.google.com/intl/ja/appengine/articles/openid.html
class OpenIDLoginHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            body = u'<a href="%s">ログアウト</a>' % \
                users.create_logout_url(self.request.uri)
        else:
            body = u"お持ちのID でログインください。<br>" + \
            "<a href='%s'>google</a><br>" % \
            users.create_login_url(federated_identity='Google.com/accounts/o8/id') + \
            "<a href='%s'>mixi</a><br>" % \
            users.create_login_url(federated_identity='mixi.jp') + \
            "<a href='%s'>biglobe</a><br>" % \
            users.create_login_url(federated_identity='openid.biglobe.ne.jp') + \
            "<a href='%s'>yahoo</a><br>" % \
            users.create_login_url(federated_identity='yahoo.co.jp')

        # http://openid.biglobe.ne.jp/forrp.html
        # 
        self.response.headers['Content-Type'] = "text/html; charset=Shift_JIS"
        self.response.out.write(template.render("templates/login.tmpl", {'body': body}))

application = webapp.WSGIApplication([
    ('/_ah/login_required', OpenIDLoginHandler)
    ], debug=True)

def main():
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
# eof
