#!/usr/bin/env python
# encoding=cp932
# parsecsv.py
# Copyright (c) 2012, 2012 Kanda.Motohiro@gmail.com
import sys
import re
import datetime
import util
import os
"""
sjis �ł́A
  File "parsecsv.py", line 56
SyntaxError: 'shift_jis' codec can't decode bytes in position 5-6: illegal multibyte sequence
�Ƃ�����B�ǂ����ANo ���P�����ɂȂ�����Ƃ��A�ەt�������Ƃ��������炵���B
cp932 �Ȃ�A�������B
"""

debug = 0

def parseSankouKikakuCsvFile(buf):
    """�G�N�Z������CSV �`���ɃG�N�X�|�[�g���ꂽ�A�V�t�gJIS�ŏ����ꂽ�A
    �����̎R�s���t�@�C���f�[�^��ǂ�ŁA�f�[�^�x�[�X�ɓ���悤�ɐ��K������
    ���̃��X�g��Ԃ��B class Kikaku �ł͂Ȃ��āA�z��B������ datetime.date
    �ւ̕ϊ��͏I����Ă���B�����́Aunicode.
    �m�F�̂��߁A��������Ȃ������s���Ԃ��B unicode �̔z��B
    buf �́A�V�t�gJIS �̕��������͂Ƃ��Ċ��҂���B
    """
    uni = buf.decode('cp932', 'replace')
    thisYear = datetime.date.today().year
    thisMonth = datetime.date.today().month

    ignored = []
    out = []
    for line in uni.split("\n"):
        # �w�b�_�[�s�͓���
        if u"�R�s�ē��ꗗ�\" in line:
            m = re.search(u"(\d*)��", line)
            if m:
                thisMonth = int(m.group(1))
            continue
        elif u" �R�s��" in line and u"����" in line: 
            continue

        # dos ���s������
        line = line.strip()
        els = line.split(",")
        if debug: print els

        # ����͓����ĂȂ����Ƃ�����
        if len(els) < 6 or els[0] == u"":
            ignored.append(line)
            continue

        try:
            no = int(els[0])
        except ValueError:
            # Do not print the line. Might not be in ascii.
            print "Invalid line in input file."
            return None, None

        # �R�s�^�C�g���́A* �͏����B
        title = els[2].replace("*", "")
        rank = els[3]
        leaders = els[4].split(u"�A")

        # ��W�I���Ƃ����̂́A���ߐ؂肪�Ȃ�
        if els[5] == u"" or els[5] == u"��":
            shimekiri = util.shimekiriNashi
        else:
            shimekiri = util.tukihi2Date(els[5],
            today=datetime.date(thisYear, thisMonth, 1))
        start, end = util.tukihi2Kikan(els[1], 
            today=datetime.date(thisYear, thisMonth, 1))

        if len(els) == 7 and els[6] != u"":
            teiin = int(els[6])
        else:
            teiin = 0

        # �����A������Adatetime.date �Ȃ�
        kikaku = (no, title, rank, start, end, shimekiri, teiin, leaders)
        out.append(kikaku)

    return out, ignored

def main():
    "���[�J�����s���āA�m�F���邽�߁B"
    if "--test" in sys.argv:
        buf = sample
    elif len(sys.argv) == 1:
        buf = sys.stdin.read()
    else:
        buf = open(sys.argv[1]).read()

    out , ignored = parseSankouKikakuCsvFile(buf)

    if os.name == 'posix':
        encoding = "utf-8"
    else:
        encoding = "cp932" # on Windows

    print "####\n%d accepted lines:\n####" % len(out)
    for kikaku in out:
        print "No=%d %s" % (kikaku[0], kikaku[1].encode(encoding, "replace")) 
    print "####\n%d ignored lines:\n####" % len(ignored)
    for line in ignored:
        print line.encode(encoding, "replace")

sample = """
20�P2�N9���@�@�@�R�s�ē��ꗗ�\�@�@�@�R�s�Q���\���e�`�w045-317-2365,,,,,,
 �R�s��,�����i�j�j,                   �R�s��,�@�����N,�@�@�@���[�_�[,�@����,���
30295,1���i�y�j,�呠���ہi�ԁj,A-A-4,���i�A����,8/29,
30296,1���i�y�j,���q�僖�����R,B-B-6.5,�x�c�A�}�{,8/26,
30278,1���i�y�j�`2���i���j,*�씪���x�c��,C-C-6.5,�x���A���c,8/20,15
30297,5���i���j,���R�O�_�x���i�w�K�j,�O�_,�؈�O�A�����Y�A�Ώ�,8/26,10
,6���i�؁j,���q���������i�����j,S-3,����A����,����,
30280,7���i���j�`9���i���j,*���䍂�x�`���䍂�x,D-D-10,�x�A������,8/23,6
,8���i�y�j,��P�x�`�_�R(��R),A-A-3,�x���A�Ό���,9/3,
30298,8���i�y�j,�����R�`�����R�`�J�~�R,B-B-6,���c�A���{�A�V�x,9/3,
30299,8���i�y�j�`9���i���j,�c��R,B-B-6,���ցA����,8/29,8
30281,8���i�y�j�`10���i���j,*�X�g�R,B-B-7,�؈�O�A��ؖ�,8/8,8
"""
if __name__ == '__main__':
    main()
# eof
