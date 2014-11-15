#!/usr/bin/env pythonw

# Web app main script
# You need Flask to run this script

import _mysql
import MySQLdb as mdb
import json
import datetime
import calendar
import decimal
from config import con, is_debug_activated, host

from flask import Flask, render_template, request
app = Flask(__name__)

app.debug = is_debug_activated

class player:
    name = ""
    data = []
    def reset(self):
        self.name = ""
        self.data = []

def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
                return float(obj)
    raise TypeError

def disp_graph(cur):
    res = ""
    p = player()
    p.reset()
    row = cur.fetchone()
    while row is not None:
        name = unicode(row[0], errors='ignore')
        if name != p.name and p.name != "":
            res = res + "{ name: " + "'" + p.name + "'" + ", data:" + json.dumps(p.data, default=decimal_default) + "},\n"
            p.reset()
        p.name = name
        score = []
        score.append(calendar.timegm(row[1].utctimetuple())*1000)
        score.append(row[2])
        p.data.append(score)
        row = cur.fetchone()
        # last player
    res = res + "{ name: " + "'" + p.name + "'" + ", data:" + json.dumps(p.data, default=decimal_default) + "}"
    return render_template("index.html", series=res)

def level_id_to_str(level_id):
    level = level_id - level_id/10*10 # keep only last digit
    episode = level_id/10
    if level == 5:
        return str(episode)
    return str(episode) + "-" + str(level)

def str_to_level_id(level_str):
    t = level_str.split('-')
    try:
        return int(t[0])*10 + int(t[1])
    except:
        # episode
        return int(t[0])*10 + 5

@app.route('/level', methods=['POST', 'GET'])
def disp_level():
    level = request.args.get('level', '')
    converted_level = str_to_level_id(level)
    cur = con.cursor()
    print converted_level
    cur.execute("select pseudo, timestamp, score*0.025 from score, players where players.id=player_id AND level_id = %s;", converted_level)
    return disp_graph(cur)

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
    app.run(host=host)

