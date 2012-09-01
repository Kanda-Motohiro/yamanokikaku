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
Parse comma separated values.
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
    �����ŁAprint �������̂́Ahttp response �ɓ���̂ŁA�G���[���b�Z�[�W
    �̂������́Aignored �ɕԂ����ƁB

    ���́Fbuf �́A�V�t�gJIS �̕�����
    �o�́F�F���ł������̔z��B���邢�́ANone
    �@�@�@�ł��Ȃ������s�̔z��B�����́Aunicode �ɂȂ��Ă���B
    """
    try:
        uni = buf.decode('cp932')
    except UnicodeDecodeError, e:
        return None, [u"�t�@�C���̕����R�[�h���A�V�t�gJIS �ł͂Ȃ��悤�ł��B" \
                        + str(e), ]

    # �t�@�C���Ɏw�肪�Ȃ���΁A�{���̔N�A�����g���B
    thisYear = datetime.date.today().year
    thisMonth = datetime.date.today().month

    ignored = []
    out = []
    for i, line in enumerate(uni.split("\n")):
        # �w�b�_�[�s�͓���
        if u"�R�s�ē��ꗗ�\" in line:
            m = re.search(u"(\d*)��", line)
            if m:
                thisMonth = int(m.group(1))
            continue
        elif u" �R�s��" in line and u"����" in line: 
            # �w�b�_�s�͓ǂݔ�΂�
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
            return None, [u"�w�肳�ꂽ�t�@�C���̌`�����ςł��B%d �s�ځB" % i, ]

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

        # �R�s�̊J�n�ƏI����
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
    "���[�J�����s���āA�R�s���t�@�C�����\�������t�H�[�}�b�g���m�F���邽�߁B"
    if os.name == 'posix':
        encoding = "utf-8"
    else:
        encoding = "cp932" # on Windows

    if "--help" in sys.argv or "-h" in sys.argv or "/?" in sys.argv:
        uni = u"�g����: %s �R�s���t�@�C��.csv" % sys.argv[0]
        print uni.encode(encoding)
        sys.exit(1)

    if "--test" in sys.argv:
        buf = sample
    elif len(sys.argv) == 1:
        buf = sys.stdin.read()
    else:
        buf = open(sys.argv[1], "rb").read()

    out , ignored = parseSankouKikakuCsvFile(buf)

    if out is None:
        print ignored[0].encode(encoding)
        sys.exit(1)
    elif len(out) == 0:
        uni = u"�P���������ł��܂���ł����B�t�@�C���̓��e���m�F���ĉ������B"
        print uni.encode(encoding)
        sys.exit(1)

    uni = u"####\n�ȉ��� %d �s���������܂����B\n####" % len(out)
    print uni.encode(encoding)
    for kikaku in out:
        print "No=%d %s" % (kikaku[0], kikaku[1].encode(encoding)) 

    uni = u"""####\n�ȉ��� %d �s�́A��t���܂���ł����B
���e���m�F���āA�K�v�Ȃ�ΏC����A���̃v���O�������Ď��s�������B
####""" % len(ignored)
    print uni.encode(encoding)
    for line in ignored:
        print line.encode(encoding)

    sys.exit(0)
# end main

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
