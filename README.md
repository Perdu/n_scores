# The Great N Highscores Archive

A Flask application to run the Great N Highscores Archive. See live version here: https://ploudseeker.com:5000/.

N is a video game released in 2004. See http://www.metanetsoftware.com/.

This repo contains:
- scripts to automatically download N 1.4 highscores and their demo data into a database,
- the Web application to display all that information in various interesting ways.

## Install

If you want to install the app on your server:
- create database by executing `database.sql`;
- create database user and give it access right to the `n_scores2` catabase:
```sql
CREATE USER '<user>'@localhost IDENTIFIED BY '<password>'
GRANT ALL ON n_scores2.* TO '<user>'@localhost
```
### Scores downloading
- fill `config.py.example` and rename it `config.py`
- In your crontab, add lines to execute `auto_download.py` every hour with option `--fill-score-unique` every hour and with option `--fill-score` every day. `--fill-score` downloads a copy of all scores every time, so you don't want to execute it too often. On the other hand, `--fill-score-unique` only downloads new scores (we need both tables in the database to speed up calculations). Add something like this (this will also save one .hs file per day):
```bash
00 * * * * python2 /path/to/n_scores/auto_download.py --fill-score-unique >/dev/null
05 05 * * * cd /path/to/save/hs_files/ && python2 /path/to/n_scores/auto_download.py --fill-score --save-hs-file
```
(Note: as the downloading library has not been converted to python3, this part requires python2)

### Web application:
- install Flask
- In python3_rewrite/, fill `config.py.example` and rename it `config.py`
- run `n_scores.py`:
```bash
python n_scores.py
```

If you want it to run inside apache2 (adds threads, which prevent the app from regularly blocking):
- fill `n_scores.wsgi.example` and rename it `n_scores.wsgi`
- follow these instructions: https://flask.palletsprojects.com/en/1.1.x/deploying/mod_wsgi/
See also give an example VirtualHost config file for apache in `apache_example_config.conf`.

## Removing hackers

Execute `python add_hacker.py <name>`. This will remove every score from the given name from the database and add it to the blacklist for future scores.

Note: hackers list is saved in NHigh's config file: `~/.nhigh/nhighconfig`
