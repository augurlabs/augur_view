from flask import Flask, render_template_string, request, session
import requests

app = Flask(__name__)

api_key = "SECRET STRING" # IE: load from file

def make_authenticated_request(endpoint, headers = {}, params = {}):
    headers["Authorization"] = f"Bearer {api_key}"

    return requests.post(endpoint, headers = auth, params = data)


home_str = """
<h1>Blank Page</h1>
<p>There's nothing here</p>
<a href="chaoss.tv/user/authorize?rurl={ url_for('login') }">Try logging in</a>
"""

@app.route("/")
def home():
    return render_template_string(home_str)

@app.route("/return")
def login():
    if session["username"]:
        return render_template_string(f"You are already logged in {session['username']}")

    oauth = request.args.get("t")

    endpoint = "chaoss.tv/api/unstable/user/generate_session"
    user_token = {"oauth_token": oauth}

    response = make_authenticated_request(endpoint, params = user_token)

    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "Validated":
            session["token"] = data["session"]
            session["username"] = data["username"]

