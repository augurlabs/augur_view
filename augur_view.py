from flask import Flask, render_template, render_template_string, request, abort
import urllib.request, json, os, math, yaml
from pathlib import Path

app = Flask(__name__)

# URL for all endpoint calls, probably won't be hardcoded for much longer
# URL = "http://zephyr.osshealth.io:5222/api/unstable"
# cacheDir = "cache/"

configFile = "config.yml"

settings = { 'approot': "/augur/", 'caching': "cache/", 'serving': "default.osshealth.io", 'paginationOffset': 25 }

def loadSettings():
    try:
        with open(configFile) as file:
            global settings
            settings = yaml.load(file, Loader=yaml.FullLoader)
    except Exception as err:
        print("Error reading application settings from [" + configFile + "], default settings kept:")
        print(err)

loadSettings()

def getSetting(key):
    if key == 'approot':
        if settings[key] == "private":
            with open(".app_root") as f:
                settings[key] = f.readline()
    return settings[key]

"""
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
"""


requested = []

def cacheFileExists(filename):
    cache_file = Path(filename)
    if cache_file.is_file() or filename in requested:
        return True
    else:
        return False

def toCacheFilename(endpoint):
    return getSetting('caching') + endpoint.replace("/", ".") + '.agcache'

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
    requestURL = getSetting('serving') + "/" + endpoint
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

"""
renderRepos:
    This function renders a list of repos using a given view, while passing query
    data along. This function also processes pagination automatically for the
    range of data provided. If a query is provided and filtering is enabled, the
    data will be filtered using the 'repo_name', 'repo_group_id' or 'rg_name'.
@PARAM:     view: String
        A string representing the template to use for displaying the repos.
@PARAM:     query: String
        The query argument from the previous page.
"""
def renderRepos(view, query, data, page = None, filter = False, pageSource = "repos/views/table"):
    PaginationOffset = getSetting('paginationOffset')
    if(data is None):
        return render_template('index.html', body="repos-" + view, title="Repos")

    if((query is not None) and filter):
        results = []
        for repo in data:
            if (query in repo["repo_name"]) or (query == str(repo["repo_group_id"])) or (query in repo["rg_name"]):
                results.append(repo)
        data = results

    pages = math.ceil(len(data) / PaginationOffset)

    if page is not None:
        page = int(page)
    else:
        page = 1

    x = PaginationOffset * (page - 1)
    data = data[x: x + PaginationOffset]

    print("Pages", pages, "Page", page, "Data", len(data))

    return render_template('index.html', body="repos-" + view, title="Repos", repos=data, query_key=query, activePage=page, pages=pages, offset=PaginationOffset, PS=pageSource, api_url=getSetting('serving'), root=getSetting('approot'))

def renderLoading(dest, query, request):
    requested.append(request)
    return render_template('index.html', body="loading", title="Loading", d=dest, query_key=query, api_url=getSetting('serving'), root=getSetting('approot'))



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

@app.route('/repos/views/repo/<id>')
def repo_repo_view(id):
    # data = requestJson('collection_status/pull_requests')

    return render_template('index.html', body="repo-info", title="Repo", repo=id, api_url=getSetting('serving'), root=getSetting('approot'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('index.html', title='404', api_url=getSetting('serving'), root=getSetting('approot')), 404

@app.route('/cache/clear')
def clear_cache():
    try:
        for f in os.listdir(getSetting('caching')):
            os.remove(os.path.join(getSetting('caching'), f))
        return render_template_string('<meta http-equiv="refresh" content="5; URL=' + getSetting('approot') + '"/><p>Cache successfully cleared</p>')
    except Exception as err:
        print(err)
        return render_template_string('<meta http-equiv="refresh" content="5; URL=' + getSetting('approot') + '"/><p>An error occurred while attempting to clear JSON cache</p>')

@app.route('/settings/reload')
def reload_settings():
    loadSettings()
    return renderLoading(getSetting('approot'), None, "repos.json")
