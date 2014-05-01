#!/usr/bin/env python
# encoding=utf-8
# session.py
# Copyright (c) 2012, 2014 Kanda.Motohiro@gmail.com
"""
"""
from django.template import Context, loader
import webapp2
from webapp2_extras import sessions


def render_template_and_write_in_sjis(handler, template_filename, body):
    # ところで、app.yaml に、テンプレートを static と書いてはいけない。
    handler.response.headers["Content-Type"] = "text/html; charset=cp932"

    t = loader.get_template(template_filename)
    uni = t.render(Context({"body": body}))
    # 丸付き数字は、シフトJIS では見えない。
    handler.response.out.write(uni.encode("cp932", "replace"))
    return


def renderKaiinTemplate(handler, logout, kaiin):
    "会員登録のフォームは、置換部分が多くて、特別。"
    if kaiin.seibetsu == u"男":
        male = "checked"
        female = ""
    else:
        female = "checked"
        male = ""

    # これは、既に登録している人にだけ、見せる。
    if kaiin.name == u"未登録":
        unsubscribe = ""
    else:
        unsubscribe = """<a href="/unsubscribe">
            このサイトへの登録を削除する</a>。"""

    handler.response.headers["Content-Type"] = "text/html; charset=cp932"
    t = loader.get_template("kaiin.tmpl")
    uni = t.render(Context({"logout": logout, "unsubscribe": unsubscribe,
        "kaiin": kaiin,
        "male": male, "female": female}))
    handler.response.out.write(uni.encode("cp932", "replace"))
    return


def renderKikakuTemplate(handler, kikaku):
    handler.response.headers["Content-Type"] = "text/html; charset=cp932"
    t = loader.get_template("kikaku.tmpl")
    uni = t.render(Context({"kikaku": kikaku}))
    handler.response.out.write(uni.encode("cp932", "replace"))
    return


# oauth サポートのため、クッキーでセッション管理をする。以下のサンプル参照。
# http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

# eof
