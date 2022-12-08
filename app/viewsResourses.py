from app import app, cssData
from flask import send_from_directory, make_response
from flask_login import current_user

@app.route('/favicon.ico')
def favicon_ico():
    return send_from_directory(app.root_path, 'static/resources/faviconF.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/favicon.png')
def favicon_png():
    return send_from_directory(app.root_path, 'static/resources/favicon.png', mimetype='image/png')

# @app.route('/background.png')
# def favicon_png():
#     return send_from_directory(app.root_path, 'static/resources/background.png', mimetype='image/png')

@app.get('/highlight.css')
def highlightStyle():
    resp = make_response(cssData)
    resp.content_type = 'text/css'
    return resp

@app.get('/index.css')
def indexStyle():
    return send_from_directory(app.root_path, 'static/styles/index.css', mimetype='text/css')

@app.get('/login.css')
def loginStyle():
    return send_from_directory(app.root_path, 'static/styles/login.css', mimetype='text/css')

@app.get('/user')
def user():
    u = {"name" : current_user.id}
    return u
