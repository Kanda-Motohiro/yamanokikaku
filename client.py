#!/usr/bin/env python
# encoding=utf-8
# Copyright (c) 2012, 2012 Kanda.Motohiro@gmail.com
"yamanokikaku のユニットテスト用のクライアント。"
import urllib
import sys
import re

host = "http://localhost:8080/"

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

def doit(op):
    print "\n#### " + op + " ####\n"
    page = urllib.urlopen(host + op)
    printOrRaise(page, 20)

mainActions = [ "", "login",
"detail", "detail?key=no-such-key",
"apply", "apply?key=no-such-key",
"cancel", "cancel?key=no-such-key",

"noSuchUrl", ""
]

def main():
    if len(sys.argv) != 1:
        for op in sys.argv[1:]:
            doit(op)
        sys.exit(0)
        
    for action in mainActions:
        doit(action)
    
if __name__ == '__main__':
    main()
# eof
