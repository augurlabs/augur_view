from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from flask import render_template, flash
from init import *
import urllib.request, json, os, math, yaml, urllib3, time, logging

""" ----------------------------------------------------------------
loadSettings:
    This function attempts to load the application settings from the config file
    (defined in init.py). It is assumed that the filename or file path defined
    during initialization is sufficient to locate the config file, and that the
    current process has read access to that file.

    If loading the config file fails, default settings are loaded via
    init_settings() and an attempt is made to write default settings to the
    provided config file.
"""
def loadSettings():
    try:
        with open(configFile) as file:
            global settings
            settings = yaml.load(file, Loader=yaml.FullLoader)
    except Exception as err:
        logging.error(f"An exception occurred reading from [{configFile}], default settings kept:")
        logging.error(err)
        init_settings()
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
"""
def toCacheFilename(endpoint):
    return endpoint.replace("/", ".").replace("?", "_").replace("=", "_") + '.agcache'

def toCacheFilepath(endpoint):
    return getSetting('caching') + toCacheFilename(endpoint)

def toCacheURL(endpoint):
    return getSetting('approot') + toCacheFilepath(endpoint)

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
    filename = toCacheFilepath(endpoint)
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
    filename = toCacheFilepath(endpoint)
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
    image_cache[image_id]['filename'] = filename
    filename = toCacheFilepath(filename)
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
    # If this request has already been fulfilled, no need to process it again
    if(repo_id in report_requests.keys()):
        return

    # initialize a new request entry to hold the resulting data
    report_requests[repo_id] = {}
    report_requests[repo_id]['complete'] = False

    """ ----------
        If the report definition could not be loaded, we cannot determine what
        files to request from the backend to compose the report. Returning here
        causes the completion status of the request to be False, which will
        display an error message when sent to the frontend.
    """
    if reports is None:
        return

    threadPools = []
    reportImages = {}
    for report in reports:
        # Reports is a dictionary of lists, so we get the size of each list
        size = len(reports[report])

        # Set up various threading components to manage image downloading
        connection_mgr = urllib3.PoolManager(maxsize=size)
        thread_pool = ThreadPoolExecutor(size)
        threadPools.append(thread_pool)

        for image in reports[report]:
            # Where should the downloaded image be stored (in cache)
            filename = toCacheFilename(f"{image['url']}?repo_id={repo_id}")
            # Where are we downloading the image from
            image_url = f"{getSetting('serving')}/{image['url']}?repo_id={repo_id}"
            # Add a request for this image to the thread pool using the download function
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
@PARAM:     sorting: String = None
        The key in the data to sort by
@PARAM:     rev: Boolean = False
        Determines if the sorted data should be displayed in descending order
@PARAM:     page: String = None
        The current page to use within pagination
@PARAM:     filter: Boolean = False
        Filter data using query
@PARAM:     pageSource: String = "repos/views/table"
        The base url to use for the page links
"""
def renderRepos(view, query, data, sorting = None, rev = False, page = None, filter = False, pageSource = "repo_table_view", sortBasis = None):
    pagination_offset = getSetting('pagination_offset')

    """ ----------
        If the data does not exist, we cannot construct the table to display on
        site. Rendering the table module without data displays an error message
    """
    if(data is None):
        return render_template('index.html', body="repos-" + view, title="Repos")

    # If a query exists and filtering is set to true, attempt to filter the data
    if((query is not None) and filter):
        results = []
        for repo in data:
            if (query in repo["repo_name"]) or (query == str(repo["repo_group_id"])) or (query in repo["rg_name"]):
                results.append(repo)
        data = results

    # Determine the maximum number of pages which can be displayed from the data
    pages = math.ceil(len(data) / pagination_offset)

    if page is not None:
        page = int(page)
    else:
        page = 1

    """ ----------
        Caller requested sorting of the data. The data is a list of dictionaries
        with numerous sortable elements, and the "sorting" parameter is assumed
        to be the key of the desired element in the dictionary by which to sort.

        We need the "or 0" here to ensure the comparison is valid for rows which
        do not have data for the requested column (we're making the assumption
        that the data type is comparable to integer 0).
    """
    if sorting is not None:
        data = sorted(data, key = lambda i: i[sorting] or 0, reverse = rev)

    """ ----------
        Here we extract a subset of the data for display on the site. First we
        calculate the start index within the data of our current "page" (x),
        then we index to that position plus the pagination offset (or page size)
        defined above. The result is a list which contains *at most* a number of
        entries equal to the pagination offset
    """
    x = pagination_offset * (page - 1)
    data = data[x: x + pagination_offset]

    return render_template('index.html', body="repos-" + view, title="Repos", repos=data, query_key=query, activePage=page, pages=pages, offset=pagination_offset, PS=pageSource, api_url=getSetting('serving'), reverse = rev, sorting = sorting)

""" ----------------------------------------------------------------
    Renders a simple page with the given message information, and optional page
    title and redirect
"""
def renderMessage(messageTitle, messageBody, title = None, redirect = None, pause = None):
    return render_template('index.html', body="notice", title=title, messageTitle=messageTitle, messageBody=messageBody, api_url=getSetting('serving'), redirect=redirect, pause=pause)

""" ----------------------------------------------------------------
"""
def render_module(module, **args):
    args.setdefault("title", "Augur View")
    args.setdefault("api_url", getSetting("serving"))
    args.setdefault("body", module)
    return render_template('index.html', **args)

""" ----------------------------------------------------------------
    No longer used
"""
# My attempt at a loading page
def renderLoading(dest, query, request):
    cache_files_requested.append(request)
    return render_template('index.html', body="loading", title="Loading", d=dest, query_key=query, api_url=getSetting('serving'))
