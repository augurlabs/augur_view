from flask import Flask, render_template, render_template_string, request, abort, jsonify, redirect, url_for, session, flash
from utils import *
from augur_view import app, login_manager
from flask_login import login_user, logout_user, current_user, login_required
from User import User
import secrets

# ROUTES -----------------------------------------------------------------------

""" ----------------------------------------------------------------
root:
    This route returns a redirect to the application root, appended
    by the provided path, if any.
"""
@app.route('/root/')
@app.route('/root/<path:path>')
def root(path=""):
    return redirect(getSetting("approot") + path)

""" ----------------------------------------------------------------
logo:
    this route returns a redirect to the application logo associated
    with the provided brand, otherwise the inverted Augur logo if no
    brand is provided.
"""
@app.route('/logo/')
@app.route('/logo/<string:brand>')
def logo(brand=None):
    if brand is None:
        return redirect(url_for('static', filename='img/augur_logo.png'))
    elif "augur" in brand:
        return logo(None)
    elif "chaoss" in brand:
        return redirect(url_for('static', filename='img/Chaoss_Logo_white.png'))
    return ""

""" ----------------------------------------------------------------
default:
table:
    This route returns the default view of the application, which
    is currently defined as the repository table view
"""
@app.route('/')
@app.route('/repos/views/table')
def repo_table_view():
    query = request.args.get('q')
    page = request.args.get('p')
    sorting = request.args.get('s')
    rev = request.args.get('r')
    if rev is not None:
        if rev == "False":
            rev = False
        elif rev == "True":
            rev = True
    else:
        rev = False

    #if not cacheFileExists("repos.json"):
    #    return renderLoading("repos/views/table", query, "repos.json")

    return renderRepos("table", query, requestJson("repos"), sorting, rev, page, True)

""" ----------------------------------------------------------------
card:
    This route returns the repository card view
"""
@app.route('/repos/views/card')
def repo_card_view():
    query = request.args.get('q')
    return renderRepos("card", query, requestJson("repos"), filter = True)

""" ----------------------------------------------------------------
groups:
    This route returns the groups table view, listing all the current
    groups in the backend
"""
@app.route('/groups')
@app.route('/groups/<group>')
def repo_groups_view(group=None):
    query = request.args.get('q')
    page = request.args.get('p')

    if(group is not None):
        query = group

    if(query is not None):
        buffer = []
        data = requestJson("repos")
        for repo in data:
            if query == str(repo["repo_group_id"]) or query in repo["rg_name"]:
                buffer.append(repo)
        return renderRepos("table", query, buffer, page = page, pageSource = "repo_groups_view")
    else:
        groups = requestJson("repo-groups")
        return render_template('index.html', body="groups-table", title="Groups", groups=groups, query_key=query, api_url=getSetting('serving'))

""" ----------------------------------------------------------------
status:
    This route returns the status view, which displays information
    about the current status of collection in the backend
"""
@app.route('/status')
def status_view():
    return render_module("status", title="Status")

""" ----------------------------------------------------------------
login:
    Under development
"""
@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        try:
            user_id = request.form.get('userID')
            user_pass = request.form.get('inputPassword')
            remember = request.form.get('remember') is not None
            if user_id is None or user_pass is None:
                raise Exception("A login issue occurred")

            user = User(user_id)

            if request.form.get('register') is not None:
                if user.exists():
                    raise Exception("That account already exists")
                elif not user.register(user_pass):
                    raise Exception("An error occurred registering your account")
                else:
                    flash("Account successfully created")

            if user.validate(user_pass) and login_user(user, remember = remember):
                flash(f"Welcome, {user_id}!")
                if "login_next" in session:
                    return redirect(session.pop("login_next"))
                return redirect(url_for('root'))
            else:
                raise Exception("Invalid login credentials")
        except Exception as e:
            flash(str(e))
    return render_module('login', title="Login")

""" ----------------------------------------------------------------
logout:
    Under development
"""
@app.route('/logout')
@login_required
def user_logout():
    logout_user()
    flash("You have been logged out")
    return redirect(url_for('root'))

""" ----------------------------------------------------------------
settings:
    Under development
"""
@app.route('/settings')
@login_required
def user_settings():
    return render_module("settings", title="Settings")

""" ----------------------------------------------------------------
report page:
    This route returns a report view of the requested repo (by ID).
"""
@app.route('/repos/views/repo/<id>')
def repo_repo_view(id):
    # For some reason, there is no reports definition (shouldn't be possible)
    if reports is None:
        return renderMessage("Report Definitions Missing", "You requested a report for a repo on this instance, but a definition for the report layout was not found.")
    data = requestJson("repos")
    repo = {}
    # Need to convert the repo id parameter to int so it's comparable
    try:
        id = int(id)
    except:
        pass
    # Finding the report object in the data so the name is accessible on the page
    for item in data:
        if item['repo_id'] == id:
            repo = item
            break

    return render_module("repo-info", reports=reports.keys(), images=reports, title="Repo", repo=repo, repo_id=id)
