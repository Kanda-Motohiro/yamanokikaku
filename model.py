#!/usr/bin/env python
# encoding=utf-8
# http://yamanokikaku.appspot.com/model.py
# Copyright (c) 2008, 2013 Kanda.Motohiro@gmail.com
# Licensed under the Apache License, Version 2.0

from google.appengine.ext import db
from util import date2Tukihi, shimekiriNashi


class Kikaku(db.Model):
    "山行企画"
    no = db.IntegerProperty(required=True)  # No. 243
    title = db.StringProperty(required=True)  # 薬師岳、雲の平
    rank = db.StringProperty()  # C-C-8.5
    start = db.DateProperty(required=True)  # 8/8
    end = db.DateProperty()  # 8/12
    shimekiri = db.DateProperty(required=True)  # 締切日 6/24
    teiin = db.IntegerProperty()  # 定員　１０人
    leaders = db.StringListProperty()  # リーダー　大友、三浦
    members = db.StringListProperty()

    def __cmp__(self, other):
        # start でソートする
        return cmp(self.start, other.start)

    def leadersMembers(self):
        leaders = ",".join(self.leaders)
        if 0 < len(self.members):
            members = ",".join(self.members)
        else:
            members = u""

        return u"リーダー:%s メンバー:%s" % (leaders, members)

    def teiinStr(self):
        # 定員、なし。いくらでも受付可能というのは、イレギュラーなので注意。
        if self.teiin == 0:
            return u"なし"
        else:
            return u"%d人" % self.teiin

    def kijitu(self):
        "日本語で示した、開始日と終了日"
        if self.start == self.end:
            end = ""
        else:
            end = u"-" + date2Tukihi(self.end)

        return date2Tukihi(self.start) + end

    def shimekiribi(self):
        # 締切日。指定なし、というのもある。
        if self.shimekiri == shimekiriNashi:
            return u"なし"
        else:
            return date2Tukihi(self.shimekiri)

    def __repr__(self):
        # no は、リンクにするので、ここでは返さない。
        return u"%s %s 期日:%s 締切日:%s 定員:%s 現在:%d人" % \
           (self.title, self.rank, self.kijitu(),
           self.shimekiribi(), self.teiinStr(), len(self.members))


class Kaiin(db.Model):
    """山岳会の会員
    会員名簿は、持ちたくなかったが、リーダーに参加者の
    緊急連絡先を伝える必要があるから、しかたないか。
    OpenID が携帯電話から使えないようなので、
    携帯端末の識別番号でログインさせることになるかも。
    """
    no = db.IntegerProperty(required=True)  # 会員番号 9000
    name = db.StringProperty(required=True)  # 田部井淳子
    openid = db.StringProperty()  # user.nickname

    seibetsu = db.StringProperty()  # 女
    tel = db.PhoneNumberProperty()  # 046-123-4567
    fax = db.PhoneNumberProperty()
    mail = db.EmailProperty()  # junko-tabei@gmail.com
    address = db.PostalAddressProperty()

    # 緊急連絡先
    kinkyuName = db.StringProperty()
    kinkyuKankei = db.StringProperty()  # 夫
    kinkyuAddress = db.PostalAddressProperty()
    kinkyuTel = db.PhoneNumberProperty()

    # 最近行った山
    saikin0 = db.StringProperty()  # 鳳凰三山　２０１２年８月
    saikin1 = db.StringProperty()
    saikin2 = db.StringProperty()

    kanyuuHoken = db.StringProperty()  # 山岳保険、ハイキング保険

    # 申し込んだ山行企画
    kikakuList = db.ListProperty(db.Key)

    def displayName(self):
        "番号と氏名を、組でよく使う。"
        return u"%d %s" % (self.no, self.name)

    def __repr__(self):
        return u"""no=%d %s %s 電話=%s fax=%s メール=%s 住所=%s
        緊急連絡先 %s %s %s %s  最近行った山 %s %s %s %s
        """ % (self.no, self.name, self.seibetsu,
        self.tel, self.fax, self.mail, self.address,
        self.kinkyuName, self.kinkyuKankei, self.kinkyuAddress,
        self.kinkyuTel,
        self.saikin0, self.saikin1, self.saikin2,
        self.kanyuuHoken)

    def updateFromDict(self, f):
        # なんか、自動的にやる方法ないんだっけ
        if "seibetsu" in f:
            self.seibetsu = f["seibetsu"]
        if "tel" in f:
            self.tel = f["tel"]
        if "fax" in f:
            self.fax = f["fax"]
        if "mail" in f:
            self.mail = f["mail"]
        if "address" in f:
            self.address = f["address"]
        if "kinkyuName" in f:
            self.kinkyuName = f["kinkyuName"]
        if "kinkyuKankei" in f:
            self.kinkyuKankei = f["kinkyuKankei"]
        if "kinkyuAddress" in f:
            self.kinkyuAddress = f["kinkyuAddress"]
        if "kinkyuTel" in f:
            self.kinkyuTel = f["kinkyuTel"]
        if "saikin0" in f:
            self.saikin0 = f["saikin0"]
        if "saikin1" in f:
            self.saikin1 = f["saikin1"]
        if "saikin2" in f:
            self.saikin2 = f["saikin2"]
        if "kanyuuHoken" in f:
            self.kanyuuHoken = f["kanyuuHoken"]


blankKaiin = Kaiin(no=0, name=u"未登録")


def parseDisplayName(dname):
    els = dname.split(None, 1)
    if len(els) != 2:
        return 0, els[0]
    return int(els[0]), els[1]


class MoushikomiRireki(db.Model):
    "申し込みの履歴。いつ、誰が、何に応募したか。"
    created = db.DateTimeProperty(auto_now_add=True)
    applyCancel = db.StringProperty()  # "apply"/"cancel"

    kaiin = db.StringProperty()

    kikakuNo = db.IntegerProperty()
    kikakuTitle = db.StringProperty()

# eof
