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
import html

from flask import Flask, render_template, request, url_for
app = Flask(__name__)

app.debug = is_debug_activated
con = None

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

def execute(query, parameters = None, return_rowcount = False, return_rows = False):
    cur = con.cursor()
    cur.execute(query, parameters)
    if return_rowcount:
        res = cur.rowcount
    elif return_rows:
        res = cur.fetchall()
    else:
        res = cur.fetchone()
    cur.close()
    return res

def connect_db():
    return mdb.connect('localhost', user, password, 'n_scores2')

def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
                return float(obj)
    raise TypeError

def disp_graph(rows):
    res = ""
    p = player()
    p.reset()
    for row in rows:
        if isinstance(row[0], int):
            name = str(row[0])
        else:
            name = html.escape(row[0])
        #    name = unicode(row[0], errors='ignore')
        if name != p.name and p.name != "":
            res = res + "{ name: " + "'" + p.name + "'" + ", data:" + json.dumps(p.data, default=decimal_default) + "},\n"
            p.reset()
        p.name = name
        score = []
        score.append(calendar.timegm(row[1].utctimetuple())*1000)
        score.append(row[2])
        p.data.append(score)
        # last player
    res = res + "{ name: " + "'" + p.name + "'" + ", data:" + json.dumps(p.data, default=decimal_default) + "}"
    return res

def level_id_to_str(level_id):
    level = int(level_id) - int(int(level_id/10)*10) # keep only last digit
    episode = int(level_id/10)
    first_0 = ""
    if episode < 10:
        first_0 = "0"
    if level == 5:
        return first_0 + str(episode)
    return first_0 + str(episode) + "-" + str(level)

def str_to_level_id(level_str):
    t = level_str.split('-')
    try:
        return int(int(t[0])*10 + int(t[1]))
    except:
        # episode
        return int(int(t[0])*10 + 5)

def score_to_str(score):
    score = str(round(int(score) * 0.025, 3))
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
        rows = execute("SELECT timestamp, level_id, score FROM score_unique WHERE pseudo = %s AND timestamp=(SELECT MIN(timestamp) FROM score_unique WHERE pseudo = %s);", (pseudo, pseudo), return_rows = True);
        row = rows[0]
        first_top_20 = ""
        first_top_20_timedelta = row[0]
        first_top_20_timestamp = row[0].strftime("%B %d, %Y")
        if first_top_20_timestamp == MIN_DATE:
            first_top_20_timestamp = "before " + MIN_DATE
        else:
            first_top_20 = '(' + str(level_id_to_str(row[1])) + ', ' + score_to_str(row[2]) + ')'
            for row in rows:
                first_top_20 += ', (' + str(level_id_to_str(row[1])) + ', ' + score_to_str(row[2]) + ')'

        rows = execute("SELECT timestamp, level_id, score FROM score_unique WHERE pseudo = %s AND place = 0 AND timestamp=(SELECT MIN(timestamp) FROM score_unique WHERE pseudo = %s AND place = 0);", (pseudo, pseudo), return_rows = True);
        first_0th = ""
        first_0th_timestamp = ""
        # Players may have a top 20 but no 0th
        row = rows[0]
        if row is not None:
            first_0th_timedelta = row[0]
            first_0th_timestamp = row[0].strftime("%B %d, %Y")
            if first_0th_timestamp == MIN_DATE:
                first_0th_timestamp = "before " + MIN_DATE
            else:
                first_0th = '(' + str(level_id_to_str(row[1])) + ', ' + score_to_str(row[2]) + ')'
                for row in rows:
                    first_0th += ', (' + str(level_id_to_str(row[1])) + ', ' + score_to_str(row[2]) + ')'
            diff_top20_0th = (first_0th_timedelta - first_top_20_timedelta).days
        else:
           first_0th_timestamp = "Never"

        rows = execute("SELECT count(DISTINCT level_id) FROM score_unique WHERE pseudo = %s AND place = 0;", (pseudo,), return_rows = True)
        nb_0th = int(rows[0][0])

        rows = execute("SELECT count(DISTINCT level_id) FROM score_unique WHERE pseudo = %s;", (pseudo,), return_rows = True)
        nb_top20 = int(rows[0][0])
        return render_template("player.html", pseudo=pseudo,
                               first_top_20_timestamp=first_top_20_timestamp,
                               first_top_20=first_top_20,
                               first_0th_timestamp=first_0th_timestamp,
                               first_0th=first_0th,
                               diff_top20_0th=diff_top20_0th,
                               nb_0th=nb_0th,
                               nb_top20=nb_top20
        )
    except Exception as err:
        print(err);
        return render_template("player.html")

@app.route('/all_scores', methods=['POST', 'GET'])
def display_all_score():
    level = html.escape(request.args.get('level', ''))
    level_id = str(str_to_level_id(level))
    player = request.args.get('player', '')
    place = request.args.get('place', '')
    if player == "" and place == "":
        rows = execute("SELECT timestamp, pseudo, score, place, ISNULL(demo) FROM score_unique WHERE level_id = %s ORDER BY score DESC", (level_id,), return_rows = True)
    elif player != "":
        rows = execute("SELECT timestamp, pseudo, score, place, ISNULL(demo) FROM score_unique WHERE level_id = %s AND pseudo = %s ORDER BY score DESC", (level_id, player), return_rows = True)
    else:
        rows = execute("SELECT timestamp, pseudo, score, place, ISNULL(demo) FROM score_unique WHERE level_id = %s AND place = %s ORDER BY score DESC", (level_id, place), return_rows = True)
    table = ""
    for row in rows:
        timestamp = str(row[0])
        pseudo = html.escape(row[1])
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
    converted_level = str(str_to_level_id(level))
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
    nb20 = execute("SELECT pseudo FROM score_unique WHERE level_id = %s GROUP BY pseudo;", (converted_level,), return_rowcount = True)

    # Number of player who ever got a 0th
    nb0 = execute("SELECT pseudo FROM score_unique WHERE level_id = %s AND place = 0 GROUP BY pseudo;", (converted_level,), return_rowcount = True)

    if diff == str(1):
        rows = execute("SELECT 'max(score) - min(score)', timestamp, (MAX(score) - min(score))*0.025 FROM score where level_id = %s group by timestamp", (converted_level,), return_rows = True)
        return render_template("all.html", series=disp_graph(rows),
                               level=level, by_place=by_place_form,
                               avg=avg_form, top=top_form, diff=diff_form,
                               nb20=nb20, nb0=nb0)
    if by_place != str(1):
        if avg == str(1):
            rows = execute("SELECT pseudo, timestamp, score*0.025 FROM score WHERE level_id = %s" + top_opt + " UNION SELECT 'average score', timestamp, AVG(score)*0.025 from score where level_id = %s" + top_opt + " GROUP BY timestamp", (converted_level, converted_level), return_rows = True)
        else:
            rows = execute("SELECT pseudo, timestamp, score*0.025 FROM score WHERE level_id = %s" + top_opt, (converted_level,), return_rows = True)
    else:
        if avg == str(1):
            rows = execute("SELECT place, timestamp, score*0.025 FROM score WHERE level_id = %s" + top_opt + " UNION SELECT 'average score', timestamp, AVG(score)*0.025 from score where level_id = %s" + top_opt + " GROUP BY timestamp ORDER BY place, timestamp", (converted_level, converted_level), return_rows = True)
        else:
            rows = execute("SELECT place, timestamp, score*0.025 FROM score WHERE level_id = %s " + top_opt + " ORDER BY place, timestamp;", (converted_level,), return_rows = True)
    return render_template("all.html", series=disp_graph(rows), level=level,
                           by_place=by_place_form, avg=avg_form, top=top_form,
                           diff=diff_form, nb20=nb20, nb0=nb0)

@app.route('/stats', methods=['POST', 'GET'])
def disp_stats():
    # 0th table
    rows = execute("SELECT COUNT(*), YEAR(timestamp) FROM score_unique WHERE place = 0 GROUP BY YEAR(timestamp);", return_rows = True)
    table_0th = {}
    for row in rows:
        table_0th[row[1]] = row[0]
    scores_series = "{ name: '0th', data: ["
    for date in sorted(table_0th):
        scores_series += "[Date.UTC(" + str(date) + ", 0, 1), " + str(table_0th[date]) + "],"
    scores_series += "]},\n"
    # 20th table
    rows = execute("SELECT COUNT(*), YEAR(timestamp) FROM score_unique GROUP BY YEAR(timestamp);", return_rows = True)
    table_20th = {}
    for row in rows:
        table_20th[row[1]] = row[0]
    scores_series += "{ name: '20th', data: ["
    for date in sorted(table_20th):
        scores_series += "[Date.UTC(" + str(date) + ", 0, 1), " + str(table_20th[date]) + "],"
    scores_series += "]},\n"
    # unique 0th table
    rows = execute("SELECT COUNT(DISTINCT level_id), YEAR(timestamp) FROM score_unique WHERE place = 0 GROUP BY YEAR(timestamp);", return_rows = True)
    table_unique_0th = {}
    for row in rows:
        table_unique_0th[row[1]] = row[0]
    scores_series += "{ name: 'Number of distinct levels whose 0th changed', data: ["
    for date in sorted(table_0th):
        scores_series += "[Date.UTC(" + str(date) + ", 0, 1), " + str(table_unique_0th[date]) + "],"
    scores_series += "]}"
    # Number of 0th
    rows = execute("SELECT COUNT(pseudo) AS a, COUNT(DISTINCT pseudo), level_id FROM score_unique WHERE place = 0 GROUP BY level_id ORDER BY a DESC;", return_rows = True)
    table = ""
    for row in rows:
        level = level_id_to_str(row[2])
        table += "<tr><td>" + str(row[0]) + "</td><td>" + str(row[1]) + "</td><td><a href='/level?level=" + level + "&top=1'>" + level + "</a></td></tr>"
    # top players graph
    rows = execute("SELECT COUNT(*) as c, YEAR(timestamp) as y, pseudo FROM score_unique WHERE place = 0 GROUP BY YEAR(timestamp), pseudo order by y, c DESC;", return_rows = True)
    table_top_players = {}
    year_i = 0
    year_cur = 2006
    players = {}
    # We only keep the top 10 players for each year (otherwise the graph will
    # be too crowded because there are too many scores in 2006)
    for row in rows:
        year = int(row[1])
        player = row[2]
        if year == year_cur and year_i >= 10 and player not in players:
            continue
        if year != year_cur:
            year_cur = year
            year_i = 0
        count = row[0]
        if player not in players:
            players[player] = {}
        players[player][year] = count
        year_i += 1
    res = ""
    last_year = year_cur
    # We create the graph by filling missing years with '0' for each player
    for player in players:
        res += "{ name: " + "'" + player + "'" + ", data: ["
        for year in range(2006, last_year + 1):
            y = int(year)
            if y in players[player]:
                count = players[player][y]
            else:
                count = 0
            res += "[Date.UTC(" + str(year) + ", 0, 1), " + str(count) + "]"
            if year != last_year:
                res += ","
        res += "]},\n"
    return render_template("stats.html", table=table, scores_series=scores_series, top_players=res)

@app.route('/new', methods=['POST', 'GET'])
def new():
    rows = execute("SELECT level_id, pseudo, score, timestamp, place from score_unique where timestamp > now() - interval 1 month ORDER BY timestamp DESC", return_rows = True)
    table = ""
    for row in rows:
        level_id = str(row[0])
        str_level_id = level_id_to_str(row[0])
        pseudo = html.escape(row[1])
        score = score_to_str(row[2])
        timestamp = str(row[3])
        place = str(row[4])
        top = str(int(place) + 1)
        row = execute("SELECT score, timestamp, ISNULL(demo) from score_unique where level_id = %s and pseudo = %s and timestamp < %s ORDER BY timestamp DESC limit 1;", (level_id, pseudo, timestamp))
        if row is not None:
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
    rows = execute("SELECT level_id, pseudo, timestamp, score, place FROM score_unique WHERE place = 0 ORDER BY timestamp DESC, level_id LIMIT 20;", return_rows = True)
    table = ""
    for row in rows:
        level_id = str(row[0])
        str_level_id = level_id_to_str(row[0])
        pseudo = html.escape(row[1])
        timestamp = str(row[2])
        score = score_to_str(row[3])
        place = str(row[4])
        top = str(int(place) + 1)
        row2 = execute("SELECT score, timestamp, ISNULL(demo) from score_unique where level_id = %s and pseudo = %s and timestamp < %s ORDER BY timestamp DESC limit 1;", (level_id, pseudo, timestamp))
        if row2 is not None:
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
            row = execute("SELECT demo FROM score_unique WHERE level_id = %s AND pseudo = %s AND timestamp = %s", (level_id, pseudo, timestamp))
        else:
            row = execute("SELECT demo FROM score_unique WHERE level_id = %s AND pseudo = %s AND score = %s", (level_id, pseudo, score))
        return render_template("demo.html", demo=row[0])
    except:
        return render_template("error.html", error="Unable to find demo.")

@app.route("/")
def index():
    return render_template("index.html")


def display_all():
    res = ""
    rows = execute("SELECT pseudo, timestamp, count(score) as c FROM score WHERE level_id < 1000 GROUP BY pseudo, timestamp HAVING c>200 ORDER BY pseudo, timestamp", return_rows = True)
    #execute("select pseudo, count(*) as c from score, players where score.player_id=id and timestamp='2007-01-01 12:53:40' group by player_id order by c DESC LIMIT 10;")
    p = player()
    for row in rows:
        #name = unicode(row[0], errors='ignore')
        name = html.escape(row[0])
        if name != p.name and p.name != "":
            res = res + "{ name: " + "'" + p.name + "'" + ", data:" + json.dumps(p.data) + "},\n"
            p.data = []
        p.name = name
        score = []
        score.append(calendar.timegm(row[1].utctimetuple())*1000)
        score.append(row[2])
        p.data.append(score)
        # last player
    res = res + "{ name: " + "'" + p.name + "'" + ", data:" + json.dumps(p.data) + "}"
    return render_template("all.html", series=res)

@app.before_request
def before_request():
    global con
    con = connect_db()

@app.after_request
def after_request(res):
    con.close()
    return res

if __name__ == "__main__":
    app.run(host=host)


