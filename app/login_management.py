from app import app, conn
from http import HTTPStatus
from flask import abort
from flask_wtf.csrf import CSRFProtect
from werkzeug.datastructures import WWWAuthenticate
from base64 import b64decode

# Add a login manager to the app
import flask_login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
# csrf =  CSRFProtect()
# csrf.init_app(app)
login_manager.login_view = "login"

# Class to store user info
# UserMixin provides us with an `id` field and the necessary
# methods (`is_authenticated`, `is_active`, `is_anonymous` and `get_id()`)
class User(flask_login.UserMixin):
    pass


# This method is called whenever the login manager needs to get
# the User object for a given user id
@login_manager.user_loader
def user_loader(user_id):
    usercheck = f"SELECT username FROM users WHERE username IN ('{user_id}');"
    c = conn.execute(usercheck)
    rows = c.fetchall()
    c.close()
    if len(rows) == 0:
        return

    # For a real app, we would load the User from a database or something
    user = User()
    user.id = user_id
    return user
