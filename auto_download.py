#!/usr/bin/env pythonw

# Auto downloader
# Downloads a new .hs file and saves it in current folder
# Usage : python auto_download.py <file>
# You need nhighlib.py from nhigh to use this script

from nhighlib import *
import datetime
import sys
# import _mysql
import MySQLdb as mdb
import getopt

import config

cur_time = str(datetime.datetime.now())
cur = None

def connect_db():
    return mdb.connect('localhost', config.user, config.password, 'n_scores2')

def usage():
    print("usage: " + sys.argv[0] + "[--fill-score][--fill-score-unique][--save-hs-file][--save-diff-only FILE][--help]")
    print("\t--fill-score: fill database with all scores. Don't do this too often (e.g. daily)")
    print("\t--fill-score-unique: fill database with new scores only. Do this often (e.g. hourly)")
    print("\t--save-hs-file: keep .hs file (readable by NHigh)")
    print("\t--save-diff-only FILE: don't save file if there is no difference with given file")
    print("\t--help: display this help message")

def run():
    global cur
    if len(sys.argv) == 1:
        usage()
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], '', ["fill-score", "fill-score-unique", "save-hs-file", "help", "save-diff-only="])
    except getopt.GetoptError as err:
        print("Error: " + str(err))
        sys.exit(1)

    fill_score_unique = False
    fill_score = False
    save_hs_file = False
    save_diff_only = False
    for o, arg in opts:
        if o == "--fill-score-unique":
            fill_score_unique = True
        elif o == "--fill-score":
            fill_score = True
        elif o == "--save-hs-file":
            save_hs_file = True
        elif o == "--save-diff-only":
            save_diff_only = True
        elif o == "--help":
            usage()
            sys.exit(0)

    print("Downloading data from metanet server...")
    downloader = HSDownloader()
    table = []
    for i in downloader:
        print(i)
    table = downloader.result()
    config.con = connect_db()
    cur = config.con.cursor()

    if fill_score_unique:
        print("Checking new demos...")
        download_demos(table.table)
    if fill_score:
        print("Adding all scores to table score...")
        fill_score(table.table)
    if save_hs_file:
        print("Saving data to file " + cur_time + ".hs")
        saveScores(table, cur_time + ".hs")
    if save_diff_only:
        print("Comparing results to file %s" % (arg))
        scores = loadScores(arg)
        if scores.table != table.table:
            print("New scores, saving to " + cur_time + ".hs")
            saveScores(table, cur_time + ".hs")
        else:
            print("No new score found, not creating new save file.")

    config.con.close()


def convert_level_nb(episode_nb, level_nb):
    return episode_nb*10 + level_nb

def download_demos(scores):
    level_nb = 0
    episode_nb = 0
    for episode in scores:
        for level in episode:
            place = 0
            for score in level:
                if score.name != '':
                    level_id = convert_level_nb(episode_nb, level_nb)
                    if not demo_exists(level_id, score.name, score.score):
                        print("New demo:", level_id, score.name, score.score)
                        add_demo(episode_nb, level_nb, score.name, score.score, cur_time, place)
                place = place + 1
            level_nb = level_nb + 1
        episode_nb = episode_nb + 1
        level_nb = 0
    config.con.commit()

def add_demo(episode_nb, level_nb, pseudo, score, timestamp, place):
    (player, score, demo) = downloadReplayByName(episode_nb, level_nb, pseudo)
    if demo == None:
        print("Error: Could not find demo for " + pseudo + " on level " + str(episode_nb) + "-" + str(level_nb), file=sys.stderr)
    if player != pseudo:
        print("Error: player name is not what was expected : %s instead of %s for level %d-%d" % (player, pseudo, episode_nb, level_nb))
    else:
        level_id = convert_level_nb(episode_nb, level_nb)
        try:
            cur.execute("INSERT INTO score_unique VALUES(%s, %s, %s, %s, %s, %s)", (level_id, pseudo, timestamp, score, place, demo))
            config.con.commit()
        except mdb.IntegrityError as err:
            print(err)

def demo_exists(level_id, pseudo, score):
    cur.execute("SELECT 1 FROM score_unique WHERE level_id=%s AND pseudo=%s AND score=%s", (level_id, pseudo, score))
    return (cur.rowcount > 0)

def add_score(score, episode_nb, level_nb, timestamp, place):
    try:
        db_level_nb = convert_level_nb(episode_nb, level_nb)
        cur.execute("INSERT INTO score VALUES(%s, %s, TIMESTAMP(%s), %s, %s)", (db_level_nb, score.name, timestamp, score.score, place))
    except mdb.IntegrityError as err:
        # There ARE duplicate entries on the scoreboard.
        # It's sad, but the best is to ignore them.
        pass

def fill_score(scores):
    level_nb = 0
    episode_nb = 0
    for episode in scores:
        for level in episode:
            place = 0
            for score in level:
                if score.name != '':
                    add_score(score, episode_nb, level_nb, cur_time, place)
                place = place + 1
            level_nb = level_nb + 1
        episode_nb = episode_nb + 1
        level_nb = 0
    config.con.commit()


if __name__=='__main__':
    run()
