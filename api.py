from flask import Flask, render_template, render_template_string, request, abort, jsonify, redirect, url_for, session, flash
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

""" ----------------------------------------------------------------
Locking request loop:
    This route will lock the current request until the
    report request completes. A json response is guaranteed.
    Assumes that the requested repo exists.
"""
@app.route('/requests/wait/<id>')
def wait_for_request(id):
    requestReports(id)
    return jsonify(report_requests[id])
