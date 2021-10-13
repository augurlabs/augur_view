from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from flask import render_template
import urllib.request, json, os, math, yaml, urllib3, time, logging

# load configuration files and initialize globals
configFile = "config.yml"
settings = { 'approot': "/", 'caching': "static/cache/", 'cache_expiry': 172800, 'serving': "default.osshealth.io", 'paginationOffset': 25, 'reports': "reports.yml" }
# default reports definition
reports = {'pull_request_reports': [{'url': 'pull_request_reports/average_commits_per_PR/', 'description': 'Average commits per pull request'}, {'url': 'pull_request_reports/average_comments_per_PR/', 'description': 'Average comments per pull request'}, {'url': 'pull_request_reports/PR_counts_by_merged_status/', 'description': 'Pull request counts by merged status'}, {'url': 'pull_request_reports/mean_response_times_for_PR/', 'description': 'Mean response times for pull requests'}, {'url': 'pull_request_reports/mean_days_between_PR_comments/', 'description': 'Mean days between pull request comments'}, {'url': 'pull_request_reports/PR_time_to_first_response/', 'description': 'Pull request time until first response'}, {'url': 'pull_request_reports/average_PR_events_for_closed_PRs/', 'description': 'Average pull request events for closed pull requests'}, {'url': 'pull_request_reports/Average_PR_duration/', 'description': 'Average pull request duration'}], 'contributor_reports': [{'url': 'contributor_reports/new_contributors_bar/', 'description': 'New contributors bar graph'}, {'url': 'contributor_reports/returning_contributors_pie_chart/', 'description': 'Returning contributors pie chart'}], 'contributor_reports_stacked': [{'url': 'contributor_reports/new_contributors_stacked_bar/', 'description': 'New contributors stacked bar chart'}, {'url': 'contributor_reports/returning_contributors_stacked_bar/', 'description': 'Returning contributors stacked bar chart'}]}

report_requests = {}

# Initialize logging
format = "%(asctime)s: %(message)s"
logging.basicConfig(filename="augur_view.log", filemode='a', format=format, level=logging.INFO, datefmt="%H:%M:%S")

""" ----------------------------------------------------------------
"""
def loadSettings():
    try:
        with open(configFile) as file:
            global settings
            settings = yaml.load(file, Loader=yaml.FullLoader)
    except Exception as err:
        logging.error(f"An exception occurred settings from [{configFile}], default settings kept:")
        logging.error(err)
        try:
            with open(configFile, 'w') as file:
                logging.info("Attempting to generate default config.yml")
                yaml.dump(settings, file)
                logging.info("Default settings file successfully generated.")
        except Exception as ioErr:
            logging.error("Error creating default config:")
            logging.error(ioErr)

""" ----------------------------------------------------------------
"""
def getSetting(key):
    return settings[key]

loadSettings()

""" ----------------------------------------------------------------
"""
def loadReports():
    global reports
    try:
        with open(getSetting("reports")) as file:
            reports = yaml.load(file, Loader=yaml.FullLoader)
            id = -1
            for report in reports:
                for image in reports[report]:
                    image['id'] = id = id + 1
        return True
    except Exception as err:
        logging.error(f"An exception occurred reading reports endpoints from [{getSetting('reports')}]:")
        logging.error(err)
        try:
            with open(getSetting("reports"), 'w') as file:
                logging.info("Attempting to generate default reports.yml")
                yaml.dump(reports, file)
                logging.info("Default reports file successfully generated.")
        except Exception as ioErr:
            logging.error("Error creating default report configuration:")
            logging.error(ioErr)
        return False

# Reports are dynamically assigned IDs during startup, which the default
# template does not have, therefore once we create the default reports.yml file,
# we must reload the reports.
if not loadReports():
    # We try once more, and then give up
    loadReports()

cache_files_requested = []

""" ----------------------------------------------------------------
"""
def cacheFileExists(filename):
    cache_file = Path(filename)
    if cache_file.is_file():
        if(getSetting('cache_expiry') > 0):
            cache_file_age = time.time() - cache_file.stat().st_mtime
            if(cache_file_age > getSetting('cache_expiry')):
                try:
                    cache_file.unlink()
                    logging.info(f"Cache file {filename} removed due to expiry")
                    return False
                except Exception as e:
                    logging.error("Error: cache file age exceeds expiry limit, but an exception occurred while attempting to remove")
                    logging.error(e)
        return True
    else:
        return False

def stripStatic(url):
    return url.replace("static/", "")

""" ----------------------------------------------------------------
toCacheFilename:
    Takes an endpoint string or
"""
def toCacheFilename(endpoint):
    return getSetting('caching') + endpoint.replace("/", ".").replace("?", "_").replace("=", "_") + '.agcache'

def toCacheURL(endpoint):
    return stripStatic(getSetting('caching')) + endpoint.replace("/", ".").replace("?", "_").replace("=", "_") + '.agcache'

""" ----------------------------------------------------------------
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
    logging.info('requesting json')
    try:
        if cacheFileExists(filename):
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
        logging.error("An exception occurred while fulfilling a json request")
        logging.error(err)

""" ----------------------------------------------------------------
"""
def requestPNG(endpoint):
    filename = toCacheFilename(endpoint)
    requestURL = getSetting('serving') + "/" + endpoint
    try:
        if cacheFileExists(filename):
            return toCacheURL(endpoint)
        else:
            urllib.request.urlretrieve(requestURL, filename)
        if filename in cache_files_requested:
            cache_files_requested.remove(filename)
        return toCacheURL(endpoint)
    except Exception as err:
        logging.error("An exception occurred while fulfilling a png request")
        logging.error(err)

""" ----------------------------------------------------------------
"""
def download(url, cmanager, filename, image_cache, image_id, repo_id = None):
    image_cache[image_id] = {}
    image_cache[image_id]['path'] = stripStatic(filename)
    if cacheFileExists(filename):
        image_cache[image_id]['exists'] = True
        return
    response = cmanager.request('GET', url)
    if "json" in response.headers['Content-Type']:
        logging.warn(f"repo {repo_id}: unexpected json response in image request")
        logging.warn(f"  response: {response.data.decode('utf-8')}")
        image_cache[image_id]['exists'] = False
        return
    if response and response.status == 200:
        image_cache[image_id]['exists'] = True
        try:
            with open(filename, 'wb') as f:
                f.write(response.data)
        except Exception as err:
            logging.error("An exception occurred writing a cache file to disk")
            logging.error(err)

""" ----------------------------------------------------------------
"""
def requestReports(repo_id):
    if(repo_id in report_requests.keys()):
        return
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
        for image in reports[report]:
            filename = toCacheFilename(f"{image['url']}?repo_id={repo_id}")
            image_url = f"{getSetting('serving')}/{image['url']}?repo_id={repo_id}"
            thread_pool.submit(download, image_url, connection_mgr, filename, reportImages, image['id'], repo_id)

    # Wait for all connections to resolve, then clean up
    for thread_pool in threadPools:
        thread_pool.shutdown()
    report_requests[repo_id]['images'] = reportImages

    # Remove the request from the queue when completed
    report_requests[repo_id]['complete'] = True

""" ----------------------------------------------------------------
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

    return render_template('index.html', body="repos-" + view, title="Repos", repos=data, query_key=query, activePage=page, pages=pages, offset=PaginationOffset, PS=pageSource, api_url=getSetting('serving'), root=getSetting('approot'))

def renderMessage(messageTitle, messageBody, title = None, redirect = None, pause = None):
    return render_template('index.html', body="notice", title=title, messageTitle=messageTitle, messageBody=messageBody, api_url=getSetting('serving'), redirect=redirect, pause=pause)

""" ----------------------------------------------------------------
    No longer used
"""
# My attempt at a loading page
def renderLoading(dest, query, request):
    cache_files_requested.append(request)
    return render_template('index.html', body="loading", title="Loading", d=dest, query_key=query, api_url=getSetting('serving'), root=getSetting('approot'))
