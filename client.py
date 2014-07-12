#!/usr/bin/env python
# encoding=utf-8
# Copyright (c) 2012, 2012 Kanda.Motohiro@gmail.com
"yamanokikaku のユニットテスト用のクライアント。"
import urllib
import urllib2
import sys
import re
try:
    import poster # これがなくても、他のところは動く。
except: pass

"""
TODO
"""
host = "http://localhost:8080/"
validKey = "ahBkZXZ-eWFtYW5va2lrYWt1cg0LEgZLaWtha3UY_AUM" # こんなの
Cookie = 'dev_appserver_login="test@example.com:True:185804764220139124118"'
headers = { }

def login():
    global headers
    headers = { "Cookie": Cookie }

def logout():
    global headers
    headers = { }

def printOrRaise(page, lines):
    for i in range(lines):
        line = page.readline()
        # 空白行はとばす
        m = re.search("^\s*$", line)
        if m: continue
        if "meta http-equiv" in line: continue
        # 落ちていたら、こちらも中止
        if "Traceback" in line or "Internal Server Error" in line:
            raise RuntimeError
        # ページは、シフトJIS で来る。
        print line.decode("cp932").encode("utf-8"),

def fetchAValidKey():
    "apply などで使う、山行企画のデータベースレコードのキーを得る。"
    global validKey

    page = urllib.urlopen(host + "debug")
    buf= page.read()
    print buf

    if (not buf.startswith("key=")) or "None" in buf:
        raise RuntimeError
    validKey = buf.replace("key=", "")

def doit(op):
    # KEY の部分を、実際のキーに置き換える。
    if "KEY" in op:
        op = op.replace("KEY", validKey)
    print "\n#### " + op + " ####\n"
    request = urllib2.Request(host + op, None, headers)
    f = urllib2.urlopen(request)
    printOrRaise(f, 20)

mainActions = [ "", "login", "table", "kaiin",
"kikaku", "kikaku?key=no-such-key", "kikaku?key=KEY",
"kikakusakujo", "kikakusakujo?key=no-such-key", "kikakusakujo?key=KEY",

"sankourireki", "sankourireki?no=no-such-key", "sankourireki?no=99999999",
"sankourireki?no=9000", # no=9000 はある。
"shimekiri", "shimekiri?key=no-such-key", "shimekiri?key=KEY",
"detail", "detail?key=no-such-key", "detail?key=KEY",
"detail?key=ahBkZXZ-eWFtYW5va2lrYWt1cg0LEgZLaWtha3UY_AUM",
"apply", "apply?key=no-such-key", "apply?key=KEY",
"apply?key=ahBkZXZ-eWFtYW5va2lrYWt1cg0LEgZLaWtha3UY_AUM",
"cancel", "cancel?key=no-such-key", "cancel?key=KEY",
"cancel?key=ahBkZXZ-eWFtYW5va2lrYWt1cg0LEgZLaWtha3UY_AUM",
"fblogin", "twlogin", "logout", "unsubscribe", 

""
]

tabeiFullRecord =  {"no":"9010", 
"name":u"田部井淳子".encode("cp932"),"seibetsu":u"女".encode("cp932"),
"tel":"123-4567", "fax":"fax-1234", "mail":"tabei@yahoo.jp", 
"address":u"横浜市中央区１−２−３".encode("cp932"),
"kinkyuName":u"田部井夫".encode("cp932"),"kinkyuKankei":u"夫".encode("cp932"),
"kinkyuAddress":u"川崎市中央区１−２−３".encode("cp932"),"kinkyuTel":"321-4567",
"saikin0":u"２０００年１月　マナスル".encode("cp932"),
"saikin1":u"２００２年１月　ダウラギリ".encode("cp932"),
"saikin2":u"２００３年１月　ホワイトゾンビ".encode("cp932"),
"kanyuuHoken":u"山岳保険".encode("cp932")}

def doKaiinPost():
    for form in (tabeiFullRecord,
 {"invalid-key":"hello"}, {"no":"1234"}, {"name":"Tanabe"},
 {"no":"hello", "name":"Tabei"},
 {"no":"9000", "name":"Tabei"},
 {"no":"9002", "name":u"田部井".encode("utf8")},
 {"no":"9003", "name":u"田部井".encode("EUCJP")},
 {"no":"9009", "name":u"田部井".encode("cp932")},
tabeiFullRecord
 ):
        print "\n#### " + str(form)[:64] + " ####\n"

        param = urllib.urlencode(form)
        request = urllib2.Request(host + "kaiin", param, headers)
        f = urllib2.urlopen(request)
        printOrRaise(f, 20)

kikakuFullRecord = { "no":"300",
"title":u"槍ヶ岳".encode("cp932"), "rank":"B-B-5.0",
"start":"8/10", "end":"8/16", "shimekiri":"7/10",
"syuugou":u"八王子駅中央線 7:30".encode("cp932"),
"CL":u"田部井".encode("cp932"), "SL":u"平山".encode("cp932"),
"course":u"上高地から横尾\n横尾から槍ヶ岳山荘\n往路を帰る".encode("cp932"),
"memo":u"あずさ１号".encode("cp932"),
}

def doKikakuPost():
    for form in (kikakuFullRecord,
 {"invalid-key":"hello"}, {"no":"200", "title":"Yarigatake", "start":"9/20"},
 {"no":"201", "title":"Oze", "start":"2014/12/30", "end":"2015/1/5"},
 {"no":"202", "title":u"尾瀬".encode("cp932"), "start":u"８月１５日".encode("cp932")},
 {"no":"203", "title":u"尾瀬".encode("utf-8"), "start":"9/21"},
 ):
        print "\n#### " + str(form)[:64] + " ####\n"

        param = urllib.urlencode(form)
        request = urllib2.Request(host + "kikaku", param, headers)
        f = urllib2.urlopen(request)
        printOrRaise(f, 20)

def postAFile(urlpath, filename):
    " from http://atlee.ca/software/poster/ "
    print "\n#### " + urlpath + " " + filename + " ####\n"
    datagen, headers = poster.encode.multipart_encode(
        {"file": open(filename, "rb")})
    request = urllib2.Request("%s%s" % (host, urlpath), "".join(datagen), headers)
    # うまいけば、ルートにリダイレクトされる。失敗したら、メッセージが返る。
    print urllib2.urlopen(request).read(160)

kaiinFiles = ("kaiin.csv", "utf-8", "euc", "kaiin.csv")
kikakuFiles = ("sankouannnai-yotei.csv", "utf-8", "euc", "sankouannnai-yotei.csv")

def main():
    if "--admin" in sys.argv:
        # app.yaml で、login:admin を外すこと
        login()
        doit("admin/deleteall") # これを最初にやる。

        for f in kaiinFiles:
            postAFile("admin/kaiin", f)
        for f in kikakuFiles:
            postAFile("admin/kikaku", f)
        sys.exit(0)
        
    elif len(sys.argv) != 1:
        for op in sys.argv[1:]:
            doit(op)
        sys.exit(0)
        
    # start
    fetchAValidKey()
    # insert new cases here.
    #login()
    #doKikakuPost()
    #logout()
    #sys.exit(0)
    # 普通の操作一覧
    for action in mainActions:
        doit(action)
    doKaiinPost()
    doKikakuPost()
    # login してからもう一度
    print "\n#### LOGGED IN ####\n"
    login()
    for action in mainActions:
        doit(action)
    doKaiinPost()
    doKikakuPost()
    logout()
    
if __name__ == "__main__":
    main()
# eof
