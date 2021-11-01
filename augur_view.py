from flask import Flask, render_template, render_template_string, request, abort, jsonify
from utils import *
import threading

app = Flask(__name__)

# ROUTES -----------------------------------------------------------------------

@app.route('/')
@app.route('/repos/views/table')
def repo_table_view():
    query = request.args.get('q')
    page = request.args.get('p')

    #if not cacheFileExists("repos.json"):
    #    return renderLoading("repos/views/table", query, "repos.json")

    data = requestJson("repos")

    return renderRepos("table", query, data, page, True)

@app.route('/repos/views/card')
def repo_card_view():
    query = request.args.get('q')
    return renderRepos("card", query, requestJson("repos"), True)

@app.route('/groups')
def repo_groups_view():
    query = request.args.get('q')
    page = request.args.get('p')

    if(query is not None):
        buffer = []
        data = requestJson("repos")
        for repo in data:
            if query == str(repo["repo_group_id"]) or query in repo["rg_name"]:
                buffer.append(repo)
        return renderRepos("table", query, buffer, page, False, "groups")
    else:
        groups = requestJson("repo-groups")
        return render_template('index.html', body="groups-table", title="Groups", groups=groups, query_key=query, api_url=getSetting('serving'), root=getSetting('approot'))

@app.route('/status')
def status_view():
    return render_template('index.html', body="status", title="Status", api_url=getSetting('serving'), root=getSetting('approot'))

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

    return render_template('index.html', body="repo-info", reports=reports.keys(), images=reports, title="Repo", repo=repo, repo_id=id, api_url=getSetting('serving'), root=getSetting('approot'))

# Code 404 response page, for pages not found
@app.errorhandler(404)
def page_not_found(error):
    return render_template('index.html', title='404', api_url=getSetting('serving'), root=getSetting('approot')), 404

# API endpoint to clear server cache
# TODO: Add verification
@app.route('/cache/clear')
def clear_cache():
    try:
        for f in os.listdir(getSetting('caching')):
            os.remove(os.path.join(getSetting('caching'), f))
        return renderMessage("Cache Cleared", "Server cache was successfully cleared", None, getSetting('approot'))
    except Exception as err:
        print(err)
        return renderMessage("Error", "An error occurred while clearing server cache.", None, getSetting('approot'), 5)

# API endpoint to reload settings from disk
@app.route('/settings/reload')
def reload_settings():
    loadSettings()
    return renderMessage("Settings Reloaded", "Server settings were successfully reloaded.", None, getSetting('approot'), 5)

""" ----------------------------------------------------------------
Locking request loop:
    This route will lock the current request until the
    report request completes. A json response is guaranteed.
    Assumes that the requested repo exists.
"""
@app.route('/requests/wait/<id>')
def wait_for_request(id):
    download_thread = threading.Thread(target=requestReports, args=(id,))
    download_thread.start()
    download_thread.join()
    return jsonify(report_requests[id])
    # if id in report_requests.keys():
    #     while not report_requests[id]['complete']:
    #         time.sleep(0.1)
    #     return jsonify(report_requests[id])
    # else:
    #     return jsonify({"exists": False})
