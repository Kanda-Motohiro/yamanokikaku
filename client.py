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
    headers = { 'Cookie': Cookie }

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
        sys.exit(1)
    validKey = buf.replace("key=", "")

def doit(op):
    # KEY の部分を、実際のキーに置き換える。
    if "KEY" in op:
        op = op.replace("KEY", validKey)
    print "\n#### " + op + " ####\n"
    request = urllib2.Request(host + op, None, headers)
    try:
        f = urllib2.urlopen(request)
    except urllib2.URLError, e:
        return
    printOrRaise(f, 20)

mainActions = [ "", "login", "table",
"detail", "detail?key=no-such-key", "detail?key=KEY",
"detail?key=ahBkZXZ-eWFtYW5va2lrYWt1cg0LEgZLaWtha3UY_AUM",
"apply", "apply?key=no-such-key", "apply?key=KEY",
"apply?key=ahBkZXZ-eWFtYW5va2lrYWt1cg0LEgZLaWtha3UY_AUM",
"cancel", "cancel?key=no-such-key", "cancel?key=KEY",
"cancel?key=ahBkZXZ-eWFtYW5va2lrYWt1cg0LEgZLaWtha3UY_AUM",

"noSuchUrl", ""
]

def doKaiinPost():
    for form in ({'invalid-key':'hello'}, {'no':'1234'}, {'name':'Tanabe'},
 {'no':'hello', 'name':'Tabei'},
 {'no':'9000', 'name':'Tabei'},
 {'no':'9002', 'name':u'田部井'.encode("utf8")},
 {'no':'9003', 'name':u'田部井'.encode("EUCJP")},
 {'no':'9009', 'name':u'田部井'.encode("cp932")}
 ):
        print "\n#### " + str(form) + " ####\n"

        param = urllib.urlencode(form)
        request = urllib2.Request(host + "kaiin", param, headers)
        try:
            f = urllib2.urlopen(request)
        except urllib2.URLError, e:
            continue
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
        
    fetchAValidKey()
    for action in mainActions:
        doit(action)
    doKaiinPost()
    print "\n#### LOGGED IN ####\n"
    login()
    for action in mainActions:
        doit(action)
    doKaiinPost()
    logout()
    
if __name__ == '__main__':
    main()
# eof
