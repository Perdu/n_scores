#!/usr/bin/env pythonw

# Auto downloader
# Downloads a new .hs file and saves it in current folder
# Usage : python auto_download.py <file>
# You need nhighlib.py from nhigh to use this script

from nhighlib import *
import datetime

def run():
    downloader = HSDownloader()
    table = []
    for i in downloader:
        print i
    table = downloader.result()
    saveScores(table, str(datetime.datetime.now()) + ".hs")

if __name__=='__main__':
    run()
