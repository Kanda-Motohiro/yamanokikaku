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
TODO poster, admin
"""
host = "http://localhost:8080/"
validKey = "ahBkZXZ-eWFtYW5va2lrYWt1cg0LEgZLaWtha3UY_AUM"

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
    global validKey

    page = urllib.urlopen(host + "debug")
    buf= page.read()
    print buf

    if (not buf.startswith("key=")) or "None" in buf:
        sys.exit(1)
    validKey = buf.replace("key=", "")

def doit(op):
    print "\n#### " + op + " ####\n"
    page = urllib.urlopen(host + op)
    printOrRaise(page, 20)

mainActions = [ "", "login", "table",
"detail", "detail?key=no-such-key", "detail?key=%s" % validKey,
"apply", "apply?key=no-such-key", "apply?key=%s" % validKey,
"cancel", "cancel?key=no-such-key", "cancel?key=%s" % validKey,

"noSuchUrl", ""
]

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
    
if __name__ == '__main__':
    main()
# eof
