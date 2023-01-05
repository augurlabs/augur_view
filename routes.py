from flask import Flask, render_template, render_template_string, request, abort, jsonify, redirect, url_for, session, flash
from utils import *
from augur_view import app, login_manager, unauthorized
from flask_login import login_user, logout_user, current_user, login_required
from server import User
from server import LoginException
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
    
    if current_user.is_authenticated:
        data = requestJson("repos", cached = False)
        user_repo_ids = current_user.query_repos()
        user_repos = []
        for repo in data:
            if repo["repo_id"] in user_repo_ids:
                user_repos.append(repo)
        
        data = user_repos or None
    else:
        data = requestJson("repos")

    #if not cacheFileExists("repos.json"):
    #    return renderLoading("repos/views/table", query, "repos.json")

    return renderRepos("table", query, data, sorting, rev, page, True)

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
@app.route('/account/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        try:
            user_id = request.form.get('username')
            remember = request.form.get('remember') is not None
            if user_id is None:
                raise LoginException("A login issue occurred")

            user = User(user_id)

            if request.form.get('register') is not None:
                if user.exists:
                    raise LoginException("User already exists")
                if not user.register(request):
                    raise LoginException("An error occurred registering your account")
                else:
                    flash("Account successfully created")

            session_key = user.validate(request)
            if session_key and login_user(user, remember = remember):
                session["aug_t"] = session_key
                flash(f"Welcome, {user_id}!")
                if "login_next" in session:
                    return redirect(session.pop("login_next"))
                return redirect(url_for('root'))
            else:
                raise LoginException("Invalid login credentials")
        except LoginException as e:
            flash(str(e))
    return render_module('login', title="Login")

""" ----------------------------------------------------------------
logout:
    Under development
"""
@app.route('/account/logout')
@login_required
def user_logout():
    logout_user()
    flash("You have been logged out")
    return redirect(url_for('root'))

@app.route('/account/delete')
@login_required
def user_delete():
    if current_user.delete():
        flash(f"Account {current_user.id} successfully removed")
        logout_user()
    else:
        flash("An error occurred removing the account")

    return redirect(url_for("root"))

@app.route('/account/update')
@login_required
def user_update_password():
    if current_user.update_password(request):
        flash(f"Account {current_user.id} successfully updated")
    else:
        flash("An error occurred updating the account")
    
    return redirect(url_for("user_settings"))

""" ----------------------------------------------------------------
settings:
    Under development
"""
@app.route('/account/settings')
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

""" ----------------------------------------------------------------
default:
table:
    This route performs external authorization for a user
"""
@app.route('/user/authorize')
def user_oauth():
    response_url = request.args.get("rurl") or session["rurl"]

    if not response_url:
        return renderMessage("Invalid Request", "It looks like some information went missing. You may need to return to the previous application and make the request again.")
    elif not current_user.is_authenticated:
        session["rurl"] = response_url
        return unauthorized()
    
    if "rurl" in session:
        session.pop("rurl")
    
    token = current_user.oauth(session["aug_t"])
    
    return redirect(f"{response_url}?t={token}")

""" ----------------------------------------------------------------
default:
table:
    This route returns a view of the selected user repo group
"""
@login_required
@app.route('/user/group/<group>')
def user_group_view(group):
    params = {}

    # NOT IMPLEMENTED
    # query = request.args.get('q')

    try:
        params["page"] = int(request.args.get('p'))
    except:
        pass

    if sort := request.args.get('s'):
        params["sort"] = sort

    rev = request.args.get('r')
    if rev is not None:
        if rev == "False":
            params["direction"] = "ASC"
        elif rev == "True":
            params["direction"] = "DESC"

    data = current_user.select_group(group, **params)

    if not data:
        return renderMessage("Error Loading Group", "Either the group you requested does not exist, or an unspecified error occurred.")

    #if not cacheFileExists("repos.json"):
    #    return renderLoading("repos/views/table", query, "repos.json")

    return render_module("repos-table", title=f"{group} Repos", repos=data, query_key=query, activePage=page, pages=pages, offset=getSetting('pagination_offset'), PS="user_group_view", reverse = rev, sorting = sorting)

""" ----------------------------------------------------------------
Admin dashboard:
    View the admin dashboard.
"""
@app.route('/dashboard')
def dashboard_view():
    empty = [
        { "title": "Placeholder", "settings": [
            { "id": "empty",
                "display_name": "Empty Entry",
                "value": "NULL",
                "description": "There's nothing here 👻"
            }
        ]}
    ]

    backend_config = requestJson("config/get", False)

    return render_template('admin-dashboard.html', sections = empty, config = backend_config)
