from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from flask import render_template
import urllib.request, json, os, math, yaml, urllib3, time, logging

# URL for all endpoint calls, probably won't be hardcoded for much longer
# URL = "http://zephyr.osshealth.io:5222/api/unstable"
# cacheDir = "cache/"

configFile = "config.yml"

settings = { 'approot': "/", 'caching': "static/cache/", 'serving': "default.osshealth.io", 'paginationOffset': 25, 'reports': "reports.yml" }

reports = None

report_requests = {}

format = "%(asctime)s: %(message)s"

logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

def loadSettings():
    try:
        with open(configFile) as file:
            global settings
            settings = yaml.load(file, Loader=yaml.FullLoader)
    except Exception as err:
        print("Error reading application settings from [" + configFile + "], default settings kept:")
        print(err)
        try:
            with open(configFile, 'w') as file:
                print("Attempting to generate default config.yml")
                yaml.dump(settings, file)
        except Exception as ioErr:
            print("Error creating default config:")
            print(ioErr)

def getSetting(key):
    if key == 'approot':
        if settings[key] == "private":
            with open(".app_root") as f:
                settings[key] = f.readline()
    return settings[key]

def loadReports():
    global reports
    try:
        with open(getSetting("reports")) as file:
            reports = yaml.load(file, Loader=yaml.FullLoader)
    except Exception as err:
        print("Error reading reports endpoints from [" + getSetting("reports") + "]:")
        print(err)

loadSettings()

loadReports()

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

cache_files_requested = []

def cacheFileExists(filename):
    cache_file = Path(filename)
    if cache_file.is_file() or filename in cache_files_requested:
        return True
    else:
        return False

def stripStatic(url):
    return url.replace("static/", "")

def toCacheFilename(endpoint):
    return getSetting('caching') + endpoint.replace("/", ".").replace("?", "_").replace("=", "_") + '.agcache'

def toCacheURL(endpoint):
    return stripStatic(getSetting('caching')) + endpoint.replace("/", ".").replace("?", "_").replace("=", "_") + '.agcache'

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
        if cacheFileExists(filename) and not filename in cache_files_requested:
            with open(filename) as f:
                data = json.load(f)
        else:
            with urllib.request.urlopen(requestURL) as url:
                data = json.loads(url.read().decode())
                with open(filename, 'w') as f:
                    json.dump(data, f)
        if filename in cache_files_requested:
            cache_files_requested.remove(filename)
        return data
    except Exception as err:
        print(err)

def requestPNG(endpoint):
    filename = toCacheFilename(endpoint)
    requestURL = getSetting('serving') + "/" + endpoint
    # print(requestURL)
    try:
        if cacheFileExists(filename) and not filename in cache_files_requested:
            return toCacheURL(endpoint)
        else:
            urllib.request.urlretrieve(requestURL, filename)
        if filename in cache_files_requested:
            cache_files_requested.remove(filename)
        return toCacheURL(endpoint)
    except Exception as err:
        print(err)

def download(url, cmanager, filename, image_cache):
    image_cache[(stripStatic(filename))] = {}
    if cacheFileExists(filename) and not filename in cache_files_requested:
        image_cache[(stripStatic(filename))]['exists'] = True
        return
    response = cmanager.request('GET', url)
    if "json" in response.headers['Content-Type']:
        logging.info("WARN: unexpected json response in image request for repo")
        logging.info(response.data.decode('utf-8'))
        image_cache[(stripStatic(filename))]['exists'] = False
        return
    if response and response.status == 200:
        image_cache[(stripStatic(filename))]['exists'] = True
        with open(filename, 'wb') as f:
            f.write(response.data)

def requestReports(repo_id):
    report_requests[repo_id] = {}
    report_requests[repo_id]['complete'] = False
    if reports is None:
        return
    threadPools = []
    reportImages = {}
    for report in reports:
        size = len(reports[report])
        connection_mgr = urllib3.PoolManager(maxsize=size)
        thread_pool = ThreadPoolExecutor(size)
        threadPools.append(thread_pool)
        for url in reports[report]:
            filename = toCacheFilename(f"{url}?repo_id={str(repo_id)}")
            url = f"{getSetting('serving')}/{url}?repo_id={str(repo_id)}"
            logging.info(url)
            thread_pool.submit(download, url, connection_mgr, filename, reportImages)

    # Wait for all connections to resolve, then clean up
    for thread_pool in threadPools:
        thread_pool.shutdown()
    report_requests[repo_id]['images'] = reportImages

    # Remove the request from the queue when completed
    report_requests[repo_id]['complete'] = True

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
@PARAM:     data: Dictionary
        The repo data to display on the page
@PARAM:     page: String = None
        The current page to use within pagination
@PARAM:     filter: Boolean = False
        Filter data using query
@PARAM:     pageSource: String = "repos/views/table"
        The base url to use for the page links
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

# My attempt at a loading page
def renderLoading(dest, query, request):
    cache_files_requested.append(request)
    return render_template('index.html', body="loading", title="Loading", d=dest, query_key=query, api_url=getSetting('serving'), root=getSetting('approot'))
