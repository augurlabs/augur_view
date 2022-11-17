from flask import Flask, render_template, render_template_string, request, abort, jsonify, redirect, url_for, session, flash
from flask_login import current_user, login_required
from utils import *
import threading
from augur_view import app

@app.route('/cache/file/')
@app.route('/cache/file/<path:file>')
def cache(file=None):
    if file is None:
        return redirect(url_for('root', path=getSetting('caching')))
    return redirect(url_for('root', path=toCacheFilepath(file)))

# API endpoint to clear server cache
# TODO: Add verification
@app.route('/cache/clear')
def clear_cache():
    try:
        for f in os.listdir(getSetting('caching')):
            os.remove(os.path.join(getSetting('caching'), f))
        return renderMessage("Cache Cleared", "Server cache was successfully cleared", redirect="/")
    except Exception as err:
        print(err)
        return renderMessage("Error", "An error occurred while clearing server cache.",  redirect="/", pause=5)

# API endpoint to reload settings from disk
@app.route('/settings/reload')
def reload_settings():
    loadSettings()
    return renderMessage("Settings Reloaded", "Server settings were successfully reloaded.", redirect="/", pause=5)

# Request the frontend version as a JSON string
@app.route('/version')
def get_version():
    return jsonify(version)

@app.route('/account/repos/add/<path:repo_url>')
@app.route('/account/repos/add')
@login_required
def add_user_repo(repo_url = None):
    if not repo_url:
        flash("Repo or org URL must not be empty")
    elif current_user.try_add_url(repo_url):
        flash("Successfully added repo or org")
    else:
        flash("Could not add repo or org")
    
    return redirect(url_for("user_settings"))

""" ----------------------------------------------------------------
"""
@app.route('/requests/make/<path:request_endpoint>')
def make_api_request(request_endpoint):
    do_cache = True
    if request.headers.get("nocache") or request.args.get("nocache"):
        do_cache = False

    data = requestJson(request_endpoint, do_cache)
    if type(data) == tuple:
        return jsonify({"request_error": data[1]}), 400
    return jsonify(data)

""" ----------------------------------------------------------------
Locking request loop:
    This route will lock the current request until the
    report request completes. A json response is guaranteed.
    Assumes that the requested repo exists.
"""
@app.route('/requests/report/wait/<id>')
def wait_for_report_request(id):
    requestReports(id)
    return jsonify(report_requests[id])
