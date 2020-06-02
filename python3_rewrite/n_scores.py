#!/usr/bin/env pythonw

# Web app main script
# You need Flask to run this script

#import _mysql
import MySQLdb as mdb
import json
import datetime
import calendar
import decimal
from config import *
import cgi

from flask import Flask, render_template, request, url_for
app = Flask(__name__)

app.debug = is_debug_activated
con = None
cur = None

MIN_DATE = "January 20, 2006"

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

def connect_db():
    return mdb.connect('localhost', user, password, 'n_scores2')

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

def score_to_str(score):
    score = str(int(score) * 0.025)
    nb_digits = len(score.split('.')[1])
    if nb_digits == 1:
        score = score + "00"
    elif nb_digits == 2:
        score = score + "0"
    return score

@app.route('/player', methods=['POST', 'GET'])
def disp_player():
    try:
        diff_top20_0th = ""
        pseudo = request.args.get('pseudo', '')
        cur.execute("SELECT timestamp, level_id, score FROM score_unique WHERE pseudo = %s AND timestamp=(SELECT MIN(timestamp) FROM score_unique WHERE pseudo = %s);", (pseudo, pseudo));
        row = cur.fetchone()
        first_top_20 = ""
        first_top_20_timedelta = row[0]
        first_top_20_timestamp = row[0].strftime("%B %d, %Y")
        if first_top_20_timestamp == MIN_DATE:
            first_top_20_timestamp = "before " + MIN_DATE
        else:
            first_top_20 = '(' + str(level_id_to_str(row[1])) + ', ' + score_to_str(row[2]) + ')'
            row = cur.fetchone()
            while (row is not None):
                first_top_20 += ', (' + str(level_id_to_str(row[1])) + ', ' + score_to_str(row[2]) + ')'
                row = cur.fetchone()

        cur.execute("SELECT timestamp, level_id, score FROM score_unique WHERE pseudo = %s AND place = 0 AND timestamp=(SELECT MIN(timestamp) FROM score_unique WHERE pseudo = %s AND place = 0);", (pseudo, pseudo));
        first_0th = ""
        first_0th_timestamp = ""
        row = cur.fetchone()
        # Players may have a top 20 but no 0th
        if row is not None:
            first_0th_timedelta = row[0]
            first_0th_timestamp = row[0].strftime("%B %d, %Y")
            if first_0th_timestamp == MIN_DATE:
                first_0th_timestamp = "before " + MIN_DATE
            else:
                first_0th = '(' + str(level_id_to_str(row[1])) + ', ' + score_to_str(row[2]) + ')'
                row = cur.fetchone()
                while (row is not None):
                    first_0th += ', (' + str(level_id_to_str(row[1])) + ', ' + score_to_str(row[2]) + ')'
                    row = cur.fetchone()
            diff_top20_0th = (first_0th_timedelta - first_top_20_timedelta).days
        else:
            first_0th_timestamp = "Never"
        return render_template("player.html", pseudo=pseudo,
                               first_top_20_timestamp=first_top_20_timestamp,
                               first_top_20=first_top_20,
                               first_0th_timestamp=first_0th_timestamp,
                               first_0th=first_0th,
                               diff_top20_0th=diff_top20_0th
        )
    except Exception as err:
        print(err);
        return render_template("player.html")

@app.route('/all_scores', methods=['POST', 'GET'])
def display_all_score():
    level = cgi.escape(request.args.get('level', ''))
    level_id = str_to_level_id(level)
    player = request.args.get('player', '')
    place = request.args.get('place', '')
    if player == "" and place == "":
        cur.execute("SELECT timestamp, pseudo, score, place, ISNULL(demo) FROM score_unique WHERE level_id = %s ORDER BY score DESC", (level_id))
    elif player != "":
        cur.execute("SELECT timestamp, pseudo, score, place, ISNULL(demo) FROM score_unique WHERE level_id = %s AND pseudo = %s ORDER BY score DESC", (level_id, player))
    else:
        cur.execute("SELECT timestamp, pseudo, score, place, ISNULL(demo) FROM score_unique WHERE level_id = %s AND place = %s ORDER BY score DESC", (level_id, place))
    rows = cur.fetchall()
    table = ""
    for row in rows:
        timestamp = str(row[0])
        pseudo = cgi.escape(row[1])
        score = score_to_str(row[2])
        place = str(row[3])
        demo_exists = not bool(row[4])
        if demo_exists:
            link = "<a href='/demo?player=" + pseudo + '&level_id=' + str(level_id) + '&timestamp=' + timestamp + "'>" + score + "</a>"
        else:
            link = score
        table += "<tr><td>" + timestamp + "</td><td>" + link +"</td><td><a href='/player?pseudo=" + pseudo + "'>" + pseudo + "</a></td><td>" + place + "</td></tr>"
    return render_template("all_scores.html", table=table, level=level)

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
    if int(top) < 20 and int(top) >= 0:
        top_opt = " AND place <= " + str(top)

    # Number of player who ever got a top 20
    cur.execute("SELECT pseudo FROM score_unique WHERE level_id = %s GROUP BY pseudo;", converted_level)
    nb20 = cur.rowcount

    # Number of player who ever got a 0th
    cur.execute("SELECT pseudo FROM score_unique WHERE level_id = %s AND place = 0 GROUP BY pseudo;", converted_level)
    nb0 = cur.rowcount

    if diff == str(1):
        cur.execute("SELECT 'max(score) - min(score)', timestamp, (MAX(score) - min(score))*0.025 FROM score where level_id = %s group by timestamp", converted_level)
        return render_template("all.html", series=disp_graph(cur),
                               level=level, by_place=by_place_form,
                               avg=avg_form, top=top_form, diff=diff_form,
                               nb20=nb20, nb0=nb0)
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
    return render_template("all.html", series=disp_graph(cur), level=level,
                           by_place=by_place_form, avg=avg_form, top=top_form,
                           diff=diff_form, nb20=nb20, nb0=nb0)

@app.route('/stats', methods=['POST', 'GET'])
def disp_stats():
    # 0th table
    cur.execute("SELECT COUNT(*), YEAR(timestamp) FROM score_unique WHERE place = 0 GROUP BY YEAR(timestamp);")
    table_0th = {}
    row = cur.fetchone()
    while row is not None:
        table_0th[row[1]] = row[0]
        row = cur.fetchone()
    scores_series = "{ name: '0th', data: ["
    for date in sorted(table_0th):
        scores_series += "[Date.UTC(" + str(date) + ", 0, 1), " + str(table_0th[date]) + "],"
    scores_series += "]},\n"
    # 20th table
    cur.execute("SELECT COUNT(*), YEAR(timestamp) FROM score_unique GROUP BY YEAR(timestamp);")
    table_20th = {}
    row = cur.fetchone()
    while row is not None:
        table_20th[row[1]] = row[0]
        row = cur.fetchone()
    scores_series += "{ name: '20th', data: ["
    for date in sorted(table_20th):
        scores_series += "[Date.UTC(" + str(date) + ", 0, 1), " + str(table_20th[date]) + "],"
    scores_series += "]},\n"
    # unique 0th table
    cur.execute("SELECT COUNT(DISTINCT level_id), YEAR(timestamp) FROM score_unique WHERE place = 0 GROUP BY YEAR(timestamp);")
    table_unique_0th = {}
    row = cur.fetchone()
    while row is not None:
        table_unique_0th[row[1]] = row[0]
        row = cur.fetchone()
    scores_series += "{ name: 'Number of distinct levels whose 0th changed', data: ["
    for date in sorted(table_0th):
        scores_series += "[Date.UTC(" + str(date) + ", 0, 1), " + str(table_unique_0th[date]) + "],"
    scores_series += "]}"
    # Number of 0th
    cur.execute("SELECT COUNT(pseudo) AS a, COUNT(DISTINCT pseudo), level_id FROM score_unique WHERE place = 0 GROUP BY level_id ORDER BY a DESC;")
    table = ""
    row = cur.fetchone()
    while row is not None:
        level = level_id_to_str(row[2])
        table += "<tr><td>" + str(row[0]) + "</td><td>" + str(row[1]) + "</td><td><a href='/level?level=" + level + "&top=1'>" + level + "</a></td></tr>"
        row = cur.fetchone()
    return render_template("stats.html", table=table, scores_series=scores_series)

@app.route('/new', methods=['POST', 'GET'])
def new():
    cur.execute("SELECT level_id, pseudo, score, timestamp, place from score_unique where timestamp > now() - interval 1 month ORDER BY timestamp DESC")
    rows = cur.fetchall()
    table = ""
    for row in rows:
        level_id = str(row[0])
        str_level_id = level_id_to_str(row[0])
        pseudo = cgi.escape(row[1])
        score = score_to_str(row[2])
        timestamp = str(row[3])
        place = str(row[4])
        top = str(int(place) + 1)
        cur.execute("SELECT score, timestamp, ISNULL(demo) from score_unique where level_id = %s and pseudo = %s and timestamp < %s ORDER BY timestamp DESC limit 1;", (level_id, pseudo, timestamp))
        if cur.rowcount > 0:
            row2 = cur.fetchone()
            prev_score = score_to_str(row2[0])
            prev_date = str(row2[1])
            demo_exists = not bool(row2[2])
            if demo_exists:
                link = "<a href='/demo?player=" + pseudo + '&level_id=' + level_id + '&timestamp=' + prev_date + "'>" + prev_score + "</a>"
            else :
                link = prev_score
        else:
            prev_score = ""
            prev_date = ""
            link = ""
        table += "<tr><td>" + timestamp + "</td><td><a href='/level?level=" + str_level_id + "&top=" + top + "'>" + str_level_id + "</a></td><td><a href='/player?pseudo=" + pseudo + "'>" + pseudo + "</a></td><td>" + place + "</td><td><a href='/demo?player=" + pseudo + '&level_id=' + level_id + '&timestamp=' + timestamp + "'>" + score + "</a></td><td>" + link + "</td><td>" + prev_date + "</td></tr>"
    return render_template("new.html", table=table)

@app.route('/latest0th', methods=['POST', 'GET'])
def latest0th():
    cur.execute("SELECT level_id, pseudo, timestamp, score, place FROM score_unique WHERE place = 0 ORDER BY timestamp DESC, level_id LIMIT 20;")
    rows = cur.fetchall()
    table = ""
    for row in rows:
        level_id = str(row[0])
        str_level_id = level_id_to_str(row[0])
        pseudo = cgi.escape(row[1])
        timestamp = str(row[2])
        score = score_to_str(row[3])
        place = str(row[4])
        top = str(int(place) + 1)
        cur.execute("SELECT score, timestamp, ISNULL(demo) from score_unique where level_id = %s and pseudo = %s and timestamp < %s ORDER BY timestamp DESC limit 1;", (level_id, pseudo, timestamp))
        if cur.rowcount > 0:
            row2 = cur.fetchone()
            prev_score = score_to_str(row2[0])
            prev_date = str(row2[1])
            demo_exists = not bool(row2[2])
            if demo_exists:
                link = "<a href='/demo?player=" + pseudo + '&level_id=' + level_id + '&timestamp=' + prev_date + "'>" + prev_score + "</a>"
            else :
                link = prev_score
        else:
            prev_score = ""
            prev_date = ""
            link = ""
        table += "<tr><td>" + timestamp + "</td><td><a href='/level?level=" + str_level_id + "&top=" + top + "'>" + str_level_id + "</a></td><td><a href='/player?pseudo=" + pseudo + "'>" + pseudo + "</a></td><td>" + place + "</td><td><a href='/demo?player=" + pseudo + '&level_id=' + level_id + '&timestamp=' + timestamp + "'>" + score + "</a></td><td>" + link + "</td><td>" + prev_date + "</td></tr>"
    return render_template("latest0th.html", table=table)

@app.route('/demo', methods=['POST', 'GET'])
def demo():
    try:
        level_id = request.args.get('level_id', '')
        pseudo = request.args.get('player', '')
        timestamp = request.args.get('timestamp', '')
        score = request.args.get('score', '')
        if score == "":
            cur.execute("SELECT demo FROM score_unique WHERE level_id = %s AND pseudo = %s AND timestamp = %s", (level_id, pseudo, timestamp))
        else:
            cur.execute("SELECT demo FROM score_unique WHERE level_id = %s AND pseudo = %s AND score = %s", (level_id, pseudo, score))
        row = cur.fetchone()
        return render_template("demo.html", demo=row[0])
    except:
        return render_template("error.html", error="Unable to find demo.")

@app.route("/")
def index():
    return render_template("index.html")


def display_all():
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
    return render_template("all.html", series=res)

@app.before_request
def before_request():
    global con, cur
    con = connect_db()
    cur = con.cursor()

@app.after_request
def after_request(res):
    global con, cur
    cur.close()
    con.close()
    return res

if __name__ == "__main__":
    app.run(host=host)


