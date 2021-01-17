from flask import Flask, render_template, request
import urllib.request, json
from pathlib import Path

app = Flask(__name__)

URL = "http://zephyr.osshealth.io:5222/api/unstable"

@app.route('/')
def augur_view():
    query = request.args.get('q')

    try:
        cache_file = Path("cache/repos.json")
        if cache_file.is_file():
            with open('cache/repos.json') as f:
                data = json.load(f)
        else:
            with urllib.request.urlopen(URL + "/repos") as url:
                data = json.loads(url.read().decode())
                with open('cache/repos.json', 'w') as f:
                    json.dump(data, f)

        if(query is not None):
            results = []
            for repo in data:
                if query in repo["repo_name"]:
                    results.append(repo)
            data = results

        page = render_template('index.html', title="Repos - Augur View", repos=data, query_key=query, api_url=URL)
    except Exception as err:
        print(err)
        page = render_template('index.html')

    return page
