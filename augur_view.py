from flask import Flask, render_template, redirect, url_for, session, request
from flask_login import LoginManager
from utils import *
from url_converters import *
from User import User

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

app.secret_key = getSetting("session_key")

app.url_map.converters['list'] = ListConverter
app.url_map.converters['bool'] = BoolConverter
app.url_map.converters['json'] = JSONConverter

# Code 404 response page, for pages not found
@app.errorhandler(404)
def page_not_found(error):
    return render_template('index.html', title='404', api_url=getSetting('serving')), 404

@login_manager.unauthorized_handler
def unauthorized():
    session["login_next"] = url_for(request.endpoint, **request.args)
    return redirect(url_for('user_login'))

@login_manager.user_loader
def load_user(user_id):
    user = User(user_id)
    if not user.exists():
        return None

    # The flask_login library sets a unique session["_id"]
    # when login_user() is called successfully
    if session.get("_id") is not None:
        user.is_authenticated = True

    return user

import routes
import api
