#!/usr/bin/env python
# http://yamanokikaku.appspot.com/sjisfilter.py
# Copyright (c) 2012 Kanda.Motohiro@gmail.com
# thanks to http://d.hatena.ne.jp/gonsuzuki/20090129/1233298532
from google.appengine.ext import webapp

def sjis(body):
    return body.encode("cp932")

register = webapp.template.create_template_register()
register.filter(sjis)

# eof
