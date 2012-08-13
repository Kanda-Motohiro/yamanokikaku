#!/usr/bin/env python
# encoding=utf-8
# http://yamanokikaku.appspot.com/main.py
# Copyright (c) 2008, 2012 Kanda.Motohiro@gmail.com
import logging
import traceback
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
import os

if __debug__:
    def dbgprint(*args):
        items = list(traceback.extract_stack()[-2][:3])
        items[0] = os.path.basename(items[0])
        logging.debug(str(items) + str(args))
else:
    def dbgprint(*args): pass

# use django 1.1 if possible
# http://code.google.com/intl/ja/appengine/docs/python/tools/libraries.html
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library, _library
try:
    use_library('django', '1.1')
except _library.UnacceptableVersionError, e:
    dbgprint(e)
    pass

# http://d.hatena.ne.jp/gonsuzuki/20090129/1233298532
# send shift-jis page
webapp.template.register_template_library('sjisfilter')

class Kikaku(db.Model):
    "山行企画"
    no = db.IntegerProperty(required=True) # No. 243
    title = db.StringProperty(required=True) # 薬師岳、雲の平
    rank = db.StringProperty() # C-C-8.5
    start = db.DateTimeProperty(required=True) # 8/8
    end = db.DateTimeProperty() # 8/12
    shimekiri = db.DateTimeProperty(required=True) # 締切日 6/24
    teiin = db.IntegerProperty() # 定員　１０人
    leaders = db.ListProperty(db.String) # リーダー　大友、三浦
    members = db.ListProperty(db.String)

    def __repr__(self):
        s = self.start
        e = self.end
        return u"No.%d %s %s 期日:%s-%s 締切日:%s 定員:%d人<br>\
        リーダー:%s メンバー:%s" % \
           (self.no, self.title, self.rank, s, e, self.shimekiri, self.teiin,
           self.leaders, self.members)
# end class

def imanoKikakuItiran():
    "今の山行企画一覧をHTMLで返す。"
    out = []
    for rec in Kikaku:
        out.append(unicode(rec))
    return "<br>\n".join(out)

#
# handlers
#
class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            body = u"<a href='/_ah/login_required'>ログイン</a><br>"
        else:
            body = u'<a href="%s">ログアウト</a><br>' % \
                users.create_logout_url(self.request.uri)
        template_values = { 'body': u"工事中。<br>" + body, }
        # ところで、app.yaml に、テンプレートを static と書いてはいけない。
        self.response.headers['Content-Type'] = "text/html; charset=Shift_JIS"
        self.response.out.write(template.render("templates/main.tmpl", template_values))

class InitLoad(webapp.RequestHandler):
    def get(self):
        rec = Kikaku(no = 243, title = u"薬師岳、雲の平", rank = "C-C-8.5",
            start = 0, end = 0, shimekiri = 0, teiin = 10,
            leaders = u"大友、三浦")
        rec.put()

            
application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/initload', InitLoad)
    ], debug=True)

def main():
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
# eof
