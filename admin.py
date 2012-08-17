#!/usr/bin/env python
# encoding=utf-8
# admin.py
# Copyright (c) 2008, 2012 Kanda.Motohiro@gmail.com
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
import datetime
from main import Kikaku
from util import *

class BulkLoad(webapp.RequestHandler):
    def get(self):
        form = """BulkLoad<br>
        <form action='/admin/bulkload' method='post' enctype='multipart/form-data'>
        <input type='file' name='file'><br>
        <input type='submit' value='load'><br>
        </form>"""
        self.response.out.write('<html><body>%s</body></html>', form)

    def post(self):
        buf = self.request.get("file")
        dbgprint(buf[:64])
        kikakuList = parseSankouKikakuCsvFile(buf)
        """
        rec = Kikaku(no = 243, title = u"薬師岳、雲の平", rank = "C-C-8.5",
            start = tukihi2Date(u"8月8日"), end = tukihi2Date(u"8月12日"),
            shimekiri = tukihi2Date(u"6月24日"), teiin = 10,
            leaders = [u"大友", u"三浦"])
        rec.put()
        """
        self.response.out.write('<html><body>load done</body></html>')

application = webapp.WSGIApplication([
    ('/admin/bulkload', BulkLoad)
    ], debug=True)

def main():BulkLoad
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
# eof
