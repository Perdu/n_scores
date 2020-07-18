# n_scores
The Great N Highscores Archive

This repo contains:
- scripts to automatically download N 1.4 highscores and their demo data into a database,
- a web application to display all that information in various interesting ways.

N is a video game. Please visit http://www.metanetsoftware.com/.

## Install

If you want to install the app on your server:
- create database by executing `database.sql`;
- In your crontab, add lines to execute `auto_download.py` every hour with option `--fill-score-unique` every hour and with option `--fill-score` every day. `--fill-score` downloads a copy of all scores every time, so you don't want to execute it too often. On the other hand, `--fill-score-unique` only downloads new scores (we need both tables in the database to speed up calculations). Add something like this (this will also save one .hs file per day):
```bash
00 * * * * python /path/to/n_scores/auto_download.py --fill-score-unique >/dev/null
05 05 * * * cd /path/to/save/hs_files/ && python /path/to/n_scores/auto_download.py --fill-score --save-hs-file
```
- for the web app:
  - install flask
  - fill `config.py.example` and rename it `config.py`
  - run `index.py`:
```bash
python index.py
```

If you want it to run inside apache2 (adds threads, which prevent the app from regularly blocking):
- fill `n_scores.wsgi.example` and rename it `n_scores.wsgi`
- follow these instructions: http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/
