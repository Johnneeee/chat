from app import app, conn
from app.login_management import user_loader
from app.forms import LoginForm, RegisterForm
from time import ctime, mktime
from hashlib import sha512
import random
from flask import request, send_from_directory, render_template
import flask
from apsw import Error
from flask_login import login_required, login_user


@app.route('/')
@app.route('/index.html')
@login_required
def index_html():
    return send_from_directory(app.root_path,
                            'templates/index.html', mimetype='text/html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    form = LoginForm()
    tries = 3
    timeout = 2
    if form.is_submitted():
        print(f'Received form: {"invalid" if not form.validate() else "valid"} {form.form_errors} {form.errors}')
        print(request.form)
    if form.validate_on_submit():
        username = form.username.data
        username = username.lower()
        username = username.replace(" ", "")
        password = form.password.data

        usercheck = f"SELECT * FROM logintry WHERE username IN ('{username}');"
        c = conn.execute(usercheck)
        rows = c.fetchall()
        if len(rows) != 0:
            if rows[0][2] == tries:
                currenttime = int(ctime()[14:-8])
                lasttry = int((rows[0][3])[14:-8])
                if currenttime >= lasttry+timeout or currenttime < lasttry:  #not optimal solution but proof of concept
                    stmt = f"UPDATE logintry SET try = {tries-1}, timestamp = '{ctime()}' WHERE username = '{username}';"
                    conn.execute(stmt)
                else:
                    msg = f"you have been timed out for a total of {timeout} minutes"
                    return render_template('/login.html', form=form, msg=msg)

        usercheck = f"SELECT hashpass,salt FROM users WHERE username IN ('{username}');"
        c = conn.execute(usercheck)
        rows = c.fetchall()
        if len(rows) == 0:
            return render_template('/login.html', form=form, msg="wrong username or password")
        savedhash,savedsalt = rows[0][0],rows[0][1]
        passcheck = sha512(bytes(f'{savedsalt}{password}', "utf-8")).hexdigest()
        if savedhash == passcheck:
            user = user_loader(username)
            
            login_user(user)
            stmt = f"UPDATE users SET isActive = 1 WHERE username = '{username}';"
            conn.execute(stmt)
            stmt = f"DELETE FROM logintry WHERE username = '{username}'"
            conn.execute(stmt)
            flask.flash('Logged in successfully.')
            stmt = f"INSERT INTO sessions  (username, log, timestamp) values ('{username}', 1, '{ctime()}');"
            conn.execute(stmt)

            # if this was a real website handling real ips from different places
            # we would use the code underneath to get the location of a user
            # and store it in session data for reference if something was to happen
            # ip = request.remote_addr
            # url = f"http://ip-api.com/json/{ip}?fields=city"
            # r = requests.get(url)
            # j = json.loads(r.text)
            # city = j[city]

            next = flask.request.args.get('next')
            # is_safe_url should check if the url is safe for redirects.
            # See http://flask.pocoo.org/snippets/62/ for an example.
            if False and not is_safe_url(next):
                return flask.abort(400)
            return flask.redirect(next or flask.url_for('index_html'))
        else:
            usercheck = f"SELECT * FROM logintry WHERE username IN ('{username}');"
            c = conn.execute(usercheck)
            rows = c.fetchall()
            if len(rows) == 0:
                stmt = f"INSERT INTO logintry (username, try, timestamp) values ('{username}', 1, '{ctime()}');"
            else:
                stmt = f"UPDATE logintry SET try = {rows[0][2] + 1}, timestamp = '{ctime()}' WHERE username = '{username}';"
            conn.execute(stmt)
            msg = "wrong username or password"
            return render_template('/login.html', form=form, msg=msg)
    return render_template('/login.html', form=form, msg=msg)


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    form = RegisterForm()
    if request.method == 'POST': 
        try:
            username = form.username.data
            username = username.lower()
            username = username.replace(" ", "")
            password = form.password.data
            if len(username) == 0:
                msg = "fill out the form"
                return render_template('/register.html', form=form, msg=msg)
            
            checkpass = securepasswordcheck(password)
            if checkpass[0] == 0:
                msg = checkpass[1]
                return render_template('/register.html', form=form, msg=msg)
            
            usercheck = f"SELECT username FROM users WHERE username IN ('{username}');"
            c = conn.execute(usercheck)
            rows = c.fetchall()
            if len(rows) != 0:
                msg = "username taken"    
                return render_template('/register.html', form=form, msg=msg)
            hash,salt = hashandsalt(password)
            stmt = f"INSERT INTO users (username, hashpass, salt, isActive) values ('{username}', '{hash}', '{salt}', 0);"
            conn.execute(stmt)
            return flask.redirect(flask.url_for('login'))
        except Error as e:
            print(e)
            msg = "something went wrong"

    return render_template('/register.html',form=form, msg=msg)

def securepasswordcheck(password):
    msg = ""
    numbers = sum(c.isdigit() for c in password)
    accepted = 0
    if len(password) < 12:
        msg = "password is too small"
    elif len(password) > 64:
        msg = "password is too long"
    elif numbers < 3:
        msg = "you need atleast 3 digits"
    else:
        accepted = 1
    return [accepted,msg]

def hashandsalt(password):
    plainsalt = random.randint(0,1000000000)
    string = bytes(f"{plainsalt}{password}", "utf-8")
    hash = sha512(string).hexdigest()
    return [hash,plainsalt]
