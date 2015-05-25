#!/usr/bin/env pythonw

# Auto downloader
# Downloads a new .hs file and saves it in current folder
# Usage : python auto_download.py <file>
# You need nhighlib.py from nhigh to use this script

from nhighlib import *
import datetime
import sys
import _mysql
import MySQLdb as mdb
import config

cur_time = str(datetime.datetime.now())
cur = None

def connect_db():
    return mdb.connect('localhost', config.user, config.password, 'n_scores2')

def run():
    global cur
    downloader = HSDownloader()
    table = []
    for i in downloader:
        print i
    table = downloader.result()
    saveScores(table, cur_time + ".hs")
    if len(sys.argv) > 1 and sys.argv[1] == "--save-demos":
        config.con = connect_db()
        cur = config.con.cursor()
        print "Checking new demos..."
        download_demos(table.table)

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
                        print "New demo:", level_id, score.name, score.score
                        add_demo(episode_nb, level_nb, score.name, score.score, cur_time, place)
                place = place + 1
            level_nb = level_nb + 1
        episode_nb = episode_nb + 1
        level_nb = 0
    config.con.commit()
    config.con.close()

def add_demo(episode_nb, level_nb, pseudo, score, timestamp, place):
    (player, score, demo) = downloadReplayByName(episode_nb, level_nb, pseudo)
    if demo == None:
        print >> sys.stderr, "Error: Could not find demo for " + pseudo + " on level " + str(episode_nb) + "-" + str(level_nb)
    if player != pseudo:
        print "Error: player name is not what was expected : %s instead of %s for level %d-%d" % (player, pseudo, episode_nb, level_nb)
    else:
        level_id = convert_level_nb(episode_nb, level_nb)
        try:
            cur.execute("INSERT INTO score_unique VALUES(%s, %s, %s, %s, %s, %s)", (level_id, pseudo, timestamp, score, place, demo))
            config.con.commit()
        except mdb.IntegrityError as err:
            print err

def demo_exists(level_id, pseudo, score):
    cur.execute("SELECT 1 FROM score_unique WHERE level_id=%s AND pseudo=%s AND score=%s", (level_id, pseudo, score))
    return (cur.rowcount > 0)

# Duplicate with fill_database (TODO)
def add_score_unique(score, episode_nb, level_nb, timestamp, place):
    try:
        db_level_nb = convert_level_nb(episode_nb, level_nb)
        cur.execute("INSERT INTO score_unique VALUES(%s, %s, TIMESTAMP(%s), %s, %s)", (db_level_nb, score.name, timestamp, score.score, place))
    except mdb.IntegrityError as err:
        pass


if __name__=='__main__':
    run()
