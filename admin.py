#!/usr/bin/env python
# encoding=utf-8
# admin.py
# Copyright (c) 2008, 2012 Kanda.Motohiro@gmail.com
import os
from util import *
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library, _library
try:
    use_library('django', '1.2')
except _library.UnacceptableVersionError, e:
    dbgprint(e)
    pass

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
import datetime
import cgi
import urllib

from main import Kikaku, Kaiin
import parsecsv

class KaiinTouroku(webapp.RequestHandler):
    "会員の名簿をファイルでもらって、Kaiin に入れる。"
    def get(self):
        form = """Please select kaiin.csv file and push the 'Send' button.<br>
        <form action='/admin/kaiin' method='post' enctype='multipart/form-data'>
        <input type='file' name='file'><br>
        <input type='submit' value='Send'><br>
        </form>"""
        self.response.out.write('<html><body>%s</body></html>' % form)

    def post(self):
        form = cgi.FieldStorage()
        buf = urllib.unquote_plus(form.getfirst("file"))
        for line in buf.decode('cp932', 'replace').split("\n"):
            els = line.split(",")
            if len(els) != 3: continue
            rec = Kaiin(no=int(els[0]), name=els[1], openid=els[2])
            rec.put()

        self.redirect("/")

class BulkLoad(webapp.RequestHandler):
    "山行企画一覧をファイルでもらって、Kikaku に入れる。"
    def get(self):
        form = """Please select sankouannnai-yotei.csv file and push the 'Send' button.<br>
        <form action='/admin/bulkload' method='post' enctype='multipart/form-data'>
        <input type='file' name='file'><br>
        <input type='submit' value='Send'><br>
        </form>"""
        self.response.out.write('<html><body>%s</body></html>' % form)

    def post(self):
        # シフトJIS のファイルなので、get ではとれない。
        form = cgi.FieldStorage()
        buf = urllib.unquote_plus(form.getfirst("file"))

        dbgprint(buf[:64])

        # 文字コード変換は、この中でやる。
        kikakuList, ignored = parsecsv.parseSankouKikakuCsvFile(buf)

        # 変なファイルを渡されたら、注意。
        if kikakuList is None:
            self.response.out.write("""<html><body>
                Invalid file? Must be a csv text file.</body></html>""")
            return

        for i, k in enumerate(kikakuList):
            # 同じファイルを２回、アップロードされたら、止める。
            if i == 0:
                query =  db.GqlQuery("SELECT * FROM Kikaku WHERE no = :1 AND \
                    start = :2", k[0], k[3])
                recs = query.fetch(1)
                if recs:
                    self.response.out.write("""<html><body>
                    Duplicate found. No=%d start=%s</body></html>""" %
                    (k[0], k[3]))
                    return

            rec = Kikaku(no = k[0], title = k[1], rank = k[2],
                start = k[3], end = k[4],
                shimekiri = k[5], teiin = k[6],
                leaders = k[7])

            rec.put()
            #dbgprint("%d %s" % (k[0], k[1].encode("utf-8", "replace")))
        # for kikakuList

        dbgprint("%d kikaku loaded. %d lines ignored" % \
            (len(kikakuList), len(ignored)))
        # post なので、リロードされないようにするのが定石で、ここで
        # 結果を表示してはいけない。
        self.redirect("/")

class InitLoad(webapp.RequestHandler):
    def get(self):
        dbgprint("InitLoad")
        rec = Kikaku(no = 243, title = u"薬師岳、雲の平", rank = "C-C-8.5",
            start = tukihi2Date(u"8月8日"), end = tukihi2Date(u"8月12日"),
            shimekiri = tukihi2Date(u"6月24日"), teiin = 10,
            leaders = [u"大友", u"三浦"])
        rec.put()

        rec = Kikaku(no = 245, title = u"御岳山滝巡り", rank = "A-B-3.5",
            start = tukihi2Date(u"7月1日"), end = tukihi2Date(u"7月1日"),
            shimekiri = tukihi2Date(u"6月28日"), teiin = 0,
            leaders = [u"田辺", u"居関"])
        rec.put()
        self.response.out.write('<html><body>done</body></html>')

class DeleteAll(webapp.RequestHandler):
    def get(self):
        for rec in Kikaku.all():
            db.delete(rec)

        self.response.out.write('<html><body>delete done</body></html>')
            
application = webapp.WSGIApplication([
    ('/admin/deleteall', DeleteAll),
    ('/admin/initload', InitLoad),

    ('/admin/kaiin', KaiinTouroku),
    ('/admin/bulkload', BulkLoad)
    ], debug=True)

def main():
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
# eof
