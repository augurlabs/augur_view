from flask import Flask, render_template, render_template_string, request, abort, jsonify, redirect, url_for
from utils import *
from url_converters import *
import threading

app = Flask(__name__)

app.url_map.converters['list'] = ListConverter
app.url_map.converters['bool'] = BoolConverter
app.url_map.converters['json'] = JSONConverter

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
    is currently defines as the repository table view
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

    return render_template('index.html', body="repo-info", reports=reports.keys(), images=reports, title="Repo", repo=repo, repo_id=id, api_url=getSetting('serving'))

# Code 404 response page, for pages not found
@app.errorhandler(404)
def page_not_found(error):
    return render_template('index.html', title='404', api_url=getSetting('serving')), 404

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
        return renderMessage("Cache Cleared", "Server cache was successfully cleared", None)
    except Exception as err:
        print(err)
        return renderMessage("Error", "An error occurred while clearing server cache.", None, 5)

# API endpoint to reload settings from disk
@app.route('/settings/reload')
def reload_settings():
    loadSettings()
    return renderMessage("Settings Reloaded", "Server settings were successfully reloaded.", None, 5)

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
    
""" ----------------------------------------------------------------
Hello World example:
    This is an example demonstrating the use of modules.
"""
@app.route('/hello-world')
def hello_world():
    return render_module("hello-world")
