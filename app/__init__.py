from flask import Flask
import sys
import apsw
from apsw import Error
from pygments.formatters import HtmlFormatter
from threading import local
from secrets import token_hex
from flask_wtf.csrf import CSRFProtect

tls = local()
cssData = HtmlFormatter(nowrap=True).get_style_defs('.highlight')
conn = None

# Set up app
app = Flask(__name__)
app.secret_key = "1234" #token_hex()

# CSRFProtect(app)?????????????


try:
    conn = apsw.Connection('./tiny.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id integer PRIMARY KEY, 
        sender TEXT NOT NULL,
        recipient TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        reply INTEGER);''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id integer PRIMARY KEY, 
        username TEXT NOT NULL,
        hashpass TEXT NOT NULL,
        salt TEXT NOT NULL,
        isActive INTEGER);''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id integer PRIMARY KEY, 
        username TEXT NOT NULL,
        log INTEGER,             
        timestamp TEXT NOT NULL);''') #for log: 0 if person has logged out 1 if person logged in
    c.execute('''CREATE TABLE IF NOT EXISTS blocking (
        id integer PRIMARY KEY, 
        username TEXT NOT NULL,
        usernameBlocked TEXT NOT NULL);''')
    c.execute('''CREATE TABLE IF NOT EXISTS logintry (
        id integer PRIMARY KEY, 
        username TEXT NOT NULL,
        try INTEGER,
        timestamp TEXT NOT NULL);''')
except Error as e:
    print(e)
    sys.exit(1)

from app import viewsSites, viewsButtons, viewsResourses
