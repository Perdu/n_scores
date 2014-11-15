#!/usr/bin/env pythonw

# Web app main script
# You need Flask to run this script

import _mysql
import MySQLdb as mdb
import json
import datetime
import calendar
from config import con

from flask import Flask, render_template
app = Flask(__name__)

app.debug = True

class player:
    def jsonable(self):
        return self.__dict__
    name = ""
    data = []

@app.route("/")
def hello():
    res = ""
    cur = con.cursor()
    cur.execute("SELECT pseudo, timestamp, count(score) as c FROM score, players WHERE score.player_id=id AND level_id < 1000 GROUP BY player_id, timestamp HAVING c>200 ORDER BY pseudo, timestamp")
    #cur.execute("select pseudo, count(*) as c from score, players where score.player_id=id and timestamp='2007-01-01 12:53:40' group by player_id order by c DESC LIMIT 10;")
    p = player()
    row = cur.fetchone()    
    while row is not None:
        name = unicode(row[0], errors='ignore')
        if name != p.name and p.name != "":
            res = res + "{ name: " + "'" + p.name + "'" + ", data:" + json.dumps(p.data) + "},\n"
            p.data = []
        p.name = name
        score = []
        score.append(calendar.timegm(row[1].utctimetuple())*1000)
        score.append(row[2])
        p.data.append(score)
        row = cur.fetchone()
        # last player
    res = res + "{ name: " + "'" + p.name + "'" + ", data:" + json.dumps(p.data) + "}"
    return render_template("index.html", series=res)

if __name__ == "__main__":
    app.run()

