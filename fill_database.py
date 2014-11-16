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
    
def add_score(score, episode_nb, level_nb, timestamp, place):
    try:
        cur = con.cursor()
        db_level_nb = convert_level_nb(episode_nb, level_nb)
        cur.execute("INSERT INTO score VALUES(%s, %s, TIMESTAMP(%s), %s, %s)", (db_level_nb, score.name, timestamp, score.score, place))
    except mdb.IntegrityError as err:
        print err
    
def fill_database():
    scores = loadScores(sys.argv[1])
    level_nb = 0
    episode_nb = 0
    for episode in scores.table:
        for level in episode:
            place = 0
            for score in level:
                if score.name != '':
                    add_score(score, episode_nb, level_nb, scores.timestamp, place)
                place = place + 1
            level_nb = level_nb + 1
        episode_nb = episode_nb + 1
        level_nb = 0
    con.commit()
    con.close()

if __name__=='__main__':
    fill_database()
