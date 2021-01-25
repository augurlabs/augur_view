from flask import Flask, render_template, request
import urllib.request, json
from pathlib import Path

app = Flask(__name__)

URL = "http://zephyr.osshealth.io:5222/api/unstable"

def requestJson(endpoint):
    filename = 'cache/' + endpoint.replace("/", ".") + '.json'
    requestURL = URL + "/" + endpoint
    try:
        cache_file = Path(filename)
        if cache_file.is_file():
            with open(filename) as f:
                data = json.load(f)
        else:
            with urllib.request.urlopen(requestURL) as url:
                data = json.loads(url.read().decode())
                with open(filename, 'w') as f:
                    json.dump(data, f)
        return data
    except Exception as err:
        print(err)

@app.route('/')
def augur_view():
    query = request.args.get('q')

    data = requestJson("repos")

    if(data is None):
        return render_template('index.html')

    if(query is not None):
        results = []
        for repo in data:
            if query in repo["repo_name"]:
                results.append(repo)
        data = results

    return render_template('index.html', body="repos-card", title="Repos", repos=data, query_key=query, api_url=URL)
