from flask import Flask, render_template, render_template_string, request, abort
import urllib.request, json, os
from pathlib import Path

app = Flask(__name__)

# URL for all endpoint calls, probably won't be hardcoded for much longer
URL = "http://science.osshealth.io:5008/api/unstable"
cacheDir = "cache/"

try:
    rootPath = Path(".app_root")
    if rootPath.is_file():
        with open(".app_root") as f:
            approot = f.readline()
    else:
        approot = "/"
except Exception as err:
    print("Error reading application root from .app_root:")
    print(err)
    print("Application root set to [/]")
    approot = "/"

requested = []

def cacheFileExists(filename):
    cache_file = Path(filename)
    if cache_file.is_file() or filename in requested:
        return True
    else:
        return False

def toCacheFilename(endpoint):
    return cacheDir + endpoint.replace("/", ".") + '.json'

"""
requestJson:
    Attempts to load JSON data from cache for the given endpoint.
    If no cache file is found, a request is made to the URL for
    the given endpoint and, if successful, the resulting JSON is
    cached for future use. Cached files will be stored with all
    '/' characters replaced with '.' for filesystem compatibility.

@PARAM:     endpoint: String
        A String representation of the requested
        json endpoint (relative to the api root).

@RETURN:    data: JSON
        An object representing the JSON data read
        from either the cache file or the enpoint
        URL. Will return None if an error is
        encountered.
"""
def requestJson(endpoint):
    filename = toCacheFilename(endpoint)
    requestURL = URL + "/" + endpoint
    try:
        if cacheFileExists(filename) and not filename in requested:
            with open(filename) as f:
                data = json.load(f)
        else:
            with urllib.request.urlopen(requestURL) as url:
                data = json.loads(url.read().decode())
                with open(filename, 'w') as f:
                    json.dump(data, f)
        if filename in requested:
            requested.remove(filename)
        return data
    except Exception as err:
        print(err)

def renderRepos(view, query, data):
    if(data is None):
        return render_template('index.html', body="repos-" + view, title="Repos")

    if(query is not None):
        results = []
        for repo in data:
            if query in repo["repo_name"] or query in str(repo["repo_group_id"]) or query in repo["rg_name"]:
                results.append(repo)
        data = results

    return render_template('index.html', body="repos-" + view, title="Repos", repos=data, query_key=query, api_url=URL, root=approot)

def renderLoading(dest, query, request):
    requested.append(request)
    return render_template('index.html', body="loading", title="Loading", d=dest, query_key=query, api_url=URL, root=approot)



# ROUTES -----------------------------------------------------------------------

@app.route('/')
@app.route('/repos/views/table')
def repo_table_view():
    query = request.args.get('q')

    if not cacheFileExists("repos.json"):
        return renderLoading("repos/views/table", query, "repos.json")

    return renderRepos("table", query, requestJson("repos"))

@app.route('/repos/views/card')
def repo_card_view():
    query = request.args.get('q')
    return renderRepos("card", query, requestJson("repos"))

@app.route('/groups')
def repo_groups_view():
    query = request.args.get('q')

    groups = requestJson("repo-groups")

    if(query is not None):
        buffer = []
        data = requestJson("repos")
        for repo in data:
            if query == str(repo["repo_group_id"]) or query in repo["rg_name"]:
                buffer.append(repo)
        return renderRepos("table", None, buffer)
    else:
        return render_template('index.html', body="groups-table", title="Groups", groups=groups, query_key=query, api_url= URL, root=approot)

@app.route('/repo/view/pr')
def repo_issues_view():
    data = requestJson('collection_status/pull_requests')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('index.html', title='404', api_url=URL, root=approot), 404

@app.route('/cache/clear')
def clear_cache():
    try:
        for f in os.listdir(cacheDir):
            os.remove(os.path.join(cacheDir, f))
        return render_template_string('<meta http-equiv="refresh" content="5; URL=' + approot + '"/><p>Cache successfully cleared</p>')
    except Exception as err:
        print(err)
        return render_template_string('<meta http-equiv="refresh" content="5; URL=' + approot + '"/><p>An error occurred while attempting to clear JSON cache</p>')
