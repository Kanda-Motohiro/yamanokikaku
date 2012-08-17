#!/usr/bin/env python
# encoding=cp932
# parsecsv.py
# Copyright (c) 2012, 2012 Kanda.Motohiro@gmail.com
import sys
import re
import datetime
import util

"""
sjis では、
  File "parsecsv.py", line 56
SyntaxError: 'shift_jis' codec can't decode bytes in position 5-6: illegal multibyte sequence
といわれる。どうも、No が１文字になったやつとか、丸付き数字とかが悪いらしい。
cp932 なら、動いた。
"""

debug = 1

def parseSankouKikakuCsvFile(buf):
    """エクセルからCSV 形式にエクスポートされた、シフトJISで書かれた、
    今月の山行企画ファイルデータを読んで、データベースに入るように正規化して
    企画のリストを返す。
    確認のため、処理されなかった行も返す。
    """
    uni = buf.decode('cp932', 'replace')
    thisYear = datetime.date.today().year
    thisMonth = datetime.date.today().month

    ignored = []
    out = []
    for line in uni.split("\n"):
        if u"山行案内一覧表" in line:
            m = re.search(u"(\d*)月", line)
            if m:
                thisMonth = int(m.group(1))

            continue
        elif u" 山行名" in line and u"締切" in line: 
            continue

        # dos 改行を除く
        els = line.strip().split(",")
        if debug: print els
        # 定員は入ってないこともある
        if len(els) < 6 or els[0] == u"":
            ignored.append(line)
            continue

        no = int(els[0])
        # 山行タイトルの、* は除く。
        title = els[2].replace("*", "")
        rank = els[3]
        leaders = els[4].split(u"、")

        # 募集終了というのは、締め切りがない
        if els[5] == u"" or els[5] == u"済":
            shimekiri = None
        else:
            shimekiri = util.tukihi2Date(els[5],
            today=datetime.date(thisYear, thisMonth, 1))
        start, end = util.tukihi2Kikan(els[1], 
            today=datetime.date(thisYear, thisMonth, 1))

        if len(els) == 7 and els[6] != u"":
            teiin = int(els[6])
        else:
            teiin = 0
        kikaku = (no, title, rank, start, end, shimekiri, teiin, leaders)
        out.append(kikaku)

    return out, ignored

def main():
    if len(sys.argv) == 1:
        buf = sample
    else:
        buf = open(sys.argv[1]).read()

    out , ignored = parseSankouKikakuCsvFile(buf)
    print out
    print "ignored lines:"
    print ignored

sample = """
20１2年9月　　　山行案内一覧表　　　山行参加申込ＦＡＸ045-317-2365,,,,,,
 山行№,月日（曜）,                   山行名,　ランク,　　　リーダー,　締切,定員
30295,1日（土）,大蔵高丸（花）,A-A-4,安永、菅沼,8/29,
30296,1日（土）,笹子雁ヶ腹摺山,B-B-6.5,富田、笠本,8/26,
30278,1日（土）～2日（日）,*南八ヶ岳縦走,C-C-6.5,堀内、島田,8/20,15
30297,5日（水）,鷹取山三点支持（学習）,三点,坪井三、加藤雄、石上,8/26,10
,6日（木）,鎌倉中央公園（公園）,S-3,猪狩、西川,当日,
30280,7日（金）～9日（日）,*西穂高岳～奥穂高岳,D-D-10,堀、高橋治,8/23,6
,8日（土）,駒ケ岳～神山(低山),A-A-3,堀内、石原藤,9/3,
30298,8日（土）,麻生山～権現山～雨降山,B-B-6,岡田、杉本、新堀,9/3,
30299,8日（土）～9日（日）,苗場山,B-B-6,居関、佐治,8/29,8
30281,8日（土）～10日（月）,*森吉山,B-B-7,坪井三、鈴木茂,8/8,8
"""
if __name__ == '__main__':
    main()
# eof
