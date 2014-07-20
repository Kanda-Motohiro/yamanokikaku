#!/usr/bin/env python
# encoding=utf-8
# http://yamanokikaku.appspot.com/model.py
# Copyright (c) 2008, 2013 Kanda.Motohiro@gmail.com
# Licensed under the Apache License, Version 2.0

import datetime
from google.appengine.ext import db
from util import date2Tukihi, shimekiriNashi, dbgprint


class Kikaku(db.Model):
    "山行企画"
    no = db.IntegerProperty()  # No. 243
    title = db.StringProperty(required=True)  # 薬師岳、雲の平
    rank = db.StringProperty()  # C-C-8.5
    start = db.DateProperty()  # 8/8
    end = db.DateProperty()  # 8/12
    shimekiri = db.DateProperty()  # 締切日 6/24
    syuugou = db.StringProperty()  # 集合 八王子駅中央線ホーム7:00
    teiin = db.IntegerProperty()  # 定員　１０人
    CL = db.StringProperty()  # チーフリーダー　大友
    SL = db.StringProperty()  # サブリーダー　三浦　
    members = db.StringListProperty()
    creator = db.ReferenceProperty() # このレコードを入れた会員のキー

    chizu = db.StringProperty()  # 昭文社　槍ヶ岳
    course = db.StringProperty(multiline=True)  # 有峰から薬師小屋 4:00
    memo = db.StringProperty(multiline=True)  # 8:01 あずさ１号乗車

    def __cmp__(self, other):
        # start でソートする
        return cmp(self.start, other.start)

    def leaders(self):
        """複数のサブリーダーというのもあるから、できるだけ、ここだけ
        なおせばいいように。"""
        return "%s,%s" % (self.CL, self.SL)

    def leadersMembers(self):
        if 0 < len(self.members):
            members = ",".join(self.members)
        else:
            members = u""

        return u"リーダー:%s メンバー:%s" % (self.leaders(), members)

    def details(self):
        " repr に入りきらない詳細をリストで返す。 "
        if not self.course:
            return ()
        return (u"コース:%s" % self.course, u"MEMO:%s" % self.memo)

    def teiinStr(self):
        # 定員、なし。いくらでも受付可能というのは、イレギュラーなので注意。
        if self.teiin == 0 or self.teiin is None:
            return u"なし"
        else:
            return u"%d人" % self.teiin

    def kijitu(self):
        "日本語で示した、開始日と終了日"
        if self.start == self.end or self.end is None:
            end = ""
        else:
            end = u"-" + date2Tukihi(self.end)

        return date2Tukihi(self.start) + end

    def kaishi(self):
        """この２つは、django template で、start, end を表示すると、
        post でそれを拾った時に、datetime.strptime でパースできない
        形式になることの対策。９月が、Sept. になる。誰がこれ決めてるの？
        テンプレートで、関数って、呼べるんだっけ。
        この関数を作って、日本語表示したらそれなりに動いた。
        単純に 2014/7/15 とかの文字列を返させてもよかったかも。
        """
        if self.start is None:
            return None
        return date2Tukihi(self.start)

    def syuuryou(self):
        if self.end is None:
            return None
        return date2Tukihi(self.end)

    def shimekiribi(self):
        # 締切日。指定なし、というのもある。
        if self.shimekiri == shimekiriNashi or self.shimekiri is None:
            return u"なし"
        else:
            return date2Tukihi(self.shimekiri)

    def __repr__(self):
        # no は、リンクにするので、ここでは返さない。
        # 表形式の時など、ブラウザ画面の１行に収まる必要がある。
        return u"%s %s 期日:%s 締切日:%s 定員:%s 現在:%d人" % \
           (self.title, self.rank, self.kijitu(),
           self.shimekiribi(), self.teiinStr(), len(self.members))


blankKikaku = Kikaku(no=0, title=u"山行名を入れて下さい",
    start=datetime.date.today(), members= [])

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


def updateFromDict(obj, kwds):
    updated = False
    for key in kwds:
        if not hasattr(obj, key):
            continue
        old = getattr(obj, key)
        if old == kwds[key]:
            continue
        updated = True
        #dbgprint("%s => %s" % (old, kwds[key]))
        setattr(obj, key, kwds[key])

    return updated


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


class Config(db.Model):
    """facebook app_secret のように、ソースにハードコードして
    さらすことのできないものを置く。"""
    name = db.StringProperty()
    value = db.StringProperty()

configs = dict(facebook_app_secret="fb", twitter_consumer_secret="tw")


def loadConfig():
    for name in ("facebook_app_secret", "twitter_consumer_secret"):
        uname = unicode(name)
        recs = db.GqlQuery("SELECT * FROM Config WHERE name = :1", uname) \
            .fetch(1)
        if recs:
            value = recs[0].value
            configs[name] = value.encode("utf-8")
        else:
            dbgprint("%s not found" % name)

loadConfig()

# eof
