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

from flask import Flask, render_template, request, url_for
app = Flask(__name__)

app.debug = is_debug_activated

MIN_DATE = "January 20, 2006"

cur = con.cursor()

class player:
    name = ""
    data = []
    def reset(self):
        self.name = ""
        self.data = []

class Score:
    level_id = -1
    timestamp = ""
    pseudo = ""
    score = 0
    place = -1

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
        if isinstance(row[0], long):
            name = str(row[0])
        else:
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
    return res

def level_id_to_str(level_id):
    level = level_id - level_id/10*10 # keep only last digit
    episode = level_id/10
    first_0 = ""
    if episode < 10:
        first_0 = "0"
    if level == 5:
        return first_0 + str(episode)
    return first_0 + str(episode) + "-" + str(level)

def str_to_level_id(level_str):
    t = level_str.split('-')
    try:
        return int(t[0])*10 + int(t[1])
    except:
        # episode
        return int(t[0])*10 + 5

@app.route('/player', methods=['POST', 'GET'])
def disp_player():
    try:
        pseudo = request.args.get('pseudo', '')
        cur.execute("SELECT timestamp, level_id, score FROM score_unique WHERE pseudo = %s AND timestamp=(SELECT MIN(timestamp) FROM score_unique WHERE pseudo = %s);", (pseudo, pseudo));
        row = cur.fetchone()
        first_top_20 = ""
        first_top_20_timestamp = row[0].strftime("%B %d, %Y")
        if first_top_20_timestamp == MIN_DATE:
            first_top_20_timestamp = "before " + MIN_DATE
        else:
            first_top_20 = '(' + str(level_id_to_str(row[1])) + ', ' + str(row[2] * 0.025) + ')'
            row = cur.fetchone()
            while (row is not None):
                first_top_20 += ', (' + str(level_id_to_str(row[1])) + ', ' + str(row[2] * 0.025) + ')'
                row = cur.fetchone()

        cur.execute("SELECT timestamp, level_id, score FROM score_unique WHERE pseudo = %s AND place = 0 AND timestamp=(SELECT MIN(timestamp) FROM score_unique WHERE pseudo = %s AND place = 0);", (pseudo, pseudo));
        first_0th = ""
        first_0th_timestamp = ""
        row = cur.fetchone()
        # Players may have a top 20 but no 0th
        if row is not None:
            first_0th_timestamp = row[0].strftime("%B %d, %Y")
            if first_0th_timestamp == MIN_DATE:
                first_0th_timestamp = "before " + MIN_DATE
            else:
                first_0th = '(' + str(level_id_to_str(row[1])) + ', ' + str(row[2] * 0.025) + ')'
                row = cur.fetchone()
                while (row is not None):
                    first_0th += ', (' + str(level_id_to_str(row[1])) + ', ' + str(row[2] * 0.025) + ')'
                    row = cur.fetchone()
        else:
            first_0th_timestamp = "Never"

        return render_template("player.html", pseudo=pseudo, first_top_20_timestamp=first_top_20_timestamp, first_top_20=first_top_20, first_0th_timestamp=first_0th_timestamp, first_0th=first_0th)
    except Exception as err:
        print err;
        return render_template("player.html")

@app.route('/level', methods=['POST', 'GET'])
def disp_level():
    level = request.args.get('level', '')
    by_place = request.args.get('by_place', '')
    avg = request.args.get('avg', '')
    top = request.args.get('top', '')
    diff = request.args.get('diff', '')
    if top != "":
        top = int(top) - 1
    else:
        top = 20
    top_opt = ""
    converted_level = str_to_level_id(level)
    by_place_form = ""
    avg_form = ""
    diff_form = ""
    if by_place == str(1):
        by_place_form = "checked"
    if avg == str(1):
        avg_form = "checked"
    if diff == str(1):
        diff_form = "checked"
    top_form = int(top) + 1
    if top_form > 20:
        top_form = 20
    cur = con.cursor()
    if int(top) < 20 and int(top) >= 0:
        top_opt = " AND place <= " + str(top)

    if diff == str(1):
        cur.execute("SELECT 'max(score) - min(score)', timestamp, (MAX(score) - min(score))*0.025 FROM score where level_id = %s group by timestamp", converted_level)
        return render_template("index.html", series=disp_graph(cur), level=level, by_place=by_place_form, avg=avg_form, top=top_form, diff=diff_form)
    if by_place != str(1):
        if avg == str(1):
            cur.execute("SELECT pseudo, timestamp, score*0.025 FROM score WHERE level_id = %s" + top_opt + " UNION SELECT 'average score', timestamp, AVG(score)*0.025 from score where level_id = %s" + top_opt + " GROUP BY timestamp", (converted_level, converted_level))
        else:
            cur.execute("SELECT pseudo, timestamp, score*0.025 FROM score WHERE level_id = %s" + top_opt, converted_level)
    else:
        if avg == str(1):
            cur.execute("SELECT place, timestamp, score*0.025 FROM score WHERE level_id = %s" + top_opt + " UNION SELECT 'average score', timestamp, AVG(score)*0.025 from score where level_id = %s" + top_opt + " GROUP BY timestamp ORDER BY place, timestamp", (converted_level, converted_level))
        else:
            cur.execute("SELECT place, timestamp, score*0.025 FROM score WHERE level_id = %s " + top_opt + " ORDER BY place, timestamp;", converted_level)
    return render_template("index.html", series=disp_graph(cur), level=level, by_place=by_place_form, avg=avg_form, top=top_form, diff=diff_form)

#@app.route("/")
def hello():
    res = ""
    cur.execute("SELECT pseudo, timestamp, count(score) as c FROM score WHERE level_id < 1000 GROUP BY pseudo, timestamp HAVING c>200 ORDER BY pseudo, timestamp")
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


