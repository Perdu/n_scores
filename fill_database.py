#!/usr/bin/env pythonw

# Insert a .hs file's fata into the database
# You need nhighlib from NHigh to run this script.

from nhighlib import *
import os, sys
import re
import datetime
import _mysql
import MySQLdb as mdb
from config import con

######## app ########

def player_exists(name):
    cur = con.cursor()
    cur.execute("SELECT 1 FROM players WHERE pseudo = %s", name)
    exists = cur.rowcount
    return bool(exists)

def add_player(name):
    print "Adding player " + name
    cur = con.cursor()
    cur.execute("INSERT INTO players VALUES(0, %s, 0, 0)", name)

def convert_level_nb(episode_nb, level_nb):
    return episode_nb*10 + level_nb
    
def add_score(score, episode_nb, level_nb, timestamp):
    try:
        cur = con.cursor()
        db_level_nb = convert_level_nb(episode_nb, level_nb)
        cur.execute("SELECT id FROM players WHERE pseudo = %s", score.name)
        player_id = cur.fetchone()[0]
        cur.execute("INSERT INTO score VALUES(%s, %s, TIMESTAMP(%s), %s)", (db_level_nb, player_id, timestamp, score.score))
    except mdb.IntegrityError as err:
        print err
    
def fill_database():
    scores = loadScores(sys.argv[1])
    level_nb = 0
    episode_nb = 0
    for episode in scores.table:
        for level in episode:
            for score in level:
                if score.name != '':
                    if not player_exists(score.name):
                        add_player(score.name)
                    add_score(score, episode_nb, level_nb, scores.timestamp)
            level_nb = level_nb + 1
        episode_nb = episode_nb + 1
        level_nb = 0
    con.commit()
    con.close()

if __name__=='__main__':
    fill_database()
