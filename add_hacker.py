#!/usr/bin/env python

# Add a hacker in the config file and remove him from the database

from nhighlib import *
import datetime
import sys
import _mysql
import MySQLdb as mdb
import config

def connect_db():
    return mdb.connect('localhost', config.user, config.password, 'n_scores2')


if __name__=='__main__':
    if len(sys.argv) != 2:
        print "Usage: python add_hacker.py <name>"
        sys.exit(1)

    nhighconfig = NHighConfig()
    if sys.argv[1] in nhighconfig.ignoredPlayers:
        print "Hacker already known. Cleaning database anyway."
    else:
        nhighconfig.ignoredPlayers.append(sys.argv[1])
        nhighconfig.save()

    config.con = connect_db()
    cur = config.con.cursor()

    cur.execute("SELECT level_id, timestamp, place, score FROM score_unique WHERE pseudo = %s order by level_id, timestamp", (sys.argv[1],))
    rows = cur.fetchall()
    nb_rows = len(rows)
    i = 0
    while i < nb_rows:
        row = rows[i]
        if i + 1 < nb_rows:
            next_row = rows[i+1]
        else:
            next_row = None
        level_id = row[0]
        timestamp = row[1]
        place = row[2]
        score = row[3]
        print "Cleaning level " + str(level_id)
        if next_row != None and next_row[0] == level_id:
            # If there are several scores on a level, only updates
            # places until the date of that next score
            cur.execute("UPDATE score_unique SET place = place - 1 WHERE level_id = %s AND timestamp >= %s AND place > %s AND score <= %s AND timestamp < %s", (level_id, timestamp, place, score, next_row[1]))
            cur.execute("UPDATE score SET place = place - 1 WHERE level_id = %s AND timestamp >= %s AND place > %s AND score <= %s AND timestamp < %s", (level_id, timestamp, place, score, next_row[1]))
        else:
            cur.execute("UPDATE score_unique SET place = place - 1 WHERE level_id = %s AND timestamp >= %s AND place > %s AND score <= %s", (level_id, timestamp, place, score))
            cur.execute("UPDATE score SET place = place - 1 WHERE level_id = %s AND timestamp >= %s AND place > %s AND score <= %s", (level_id, timestamp, place, score))
        cur.execute("DELETE FROM score_unique WHERE pseudo = %s AND level_id = %s AND timestamp = %s", (sys.argv[1], level_id, timestamp))
        i = i + 1

    print "Cleaning table score"
    cur.execute("DELETE FROM score WHERE pseudo = %s", (sys.argv[1],))
    
    config.con.commit()
    config.con.close()

