from flask_login import UserMixin
# I'm using requests here to avoid circular integration with utils
import requests, time, re

""" ----------------------------------------------------------------
"""
class User(UserMixin):
    # User.api is set in utils.py
    # User.logger is set in utils.py

    @property
    def is_authenticated(self):
        return self._is_authenticated

    @is_authenticated.setter
    def is_authenticated(self, val):
        self._is_authenticated = val

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, val):
        self._is_active = val

    @property
    def is_anoymous(self):
        return self._is_anoymous

    @is_anoymous.setter
    def is_anoymous(self, val):
        self._is_anoymous = val
    
    @property
    def exists(self):
        return self._exists

    def __init__(self, id):
        # flask_login requires that the id be of type string
        self.id = str(id)
        self._exists = False
        self._is_anonymous = False
        self._is_authenticated = False
        self._is_active = False

        # Query the server for the existence of this user
        self.query_user()
    
    def query_user(self):
        if self._exists:
            # User has already been queried and verified to exist
            return True

        endpoint = User.api + "/user/query"

        response = requests.post(endpoint, params = {"username": self.id})

        if response.status_code == 200 and response.json().get("status") == True:
            self._exists = True
            return True
        
        return False

    def get_id(self):
        return self.id
    
    def query_repos(self):
        endpoint = User.api + "/user/repos"

        response = requests.post(endpoint, params = {"username": self.id})

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return data.get("repo_ids")
            else:
                User.logger.warning(f"Could not get user repos: {data.get('status')}")
        else:
            User.logger.warning(f"Could not get user repos: {response.status_code}")
    
    def try_add_url(self, url):
        result = re.search("https?:\/\/github\.com\/([[:alnum:] - _]+)\/([[:alnum:] - _]+)(.git)?\/?$", url)

        if result:
            return self.add_repo(url)
        else:
            return self.add_org(url)
    
    def add_repo(self, url):
        endpoint = User.api + "/user/add_repo"

        response = requests.post(endpoint, params = {"username": self.id, "repo_url": url})
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "Repo Added":
                return True
            else:
                User.logger.warning(f"Could not add user repo {url}: {data.get('status')}")
        else:
            User.logger.warning(f"Could not add user repo {url}: {response.status_code}")
        
        return False

    def add_org(self, url):
        endpoint = User.api + "/user/add_org"

        response = requests.post(endpoint, params = {"username": self.id, "org_url": url})
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "Org repos added":
                return True
            else:
                User.logger.warning(f"Could not add user org {url}: {data.get('status')}")
        else:
            User.logger.warning(f"Could not add user org {url}: {response.status_code}")
        
        return False


    def register(self, request):
        endpoint = User.api + "/user/create"

        data = request.form.to_dict()

        # admin creation is CLI only for now
        if "create_admin" in data:
            data.pop("create_admin")

        response = requests.post(endpoint, params = request.form.to_dict())

        if response.status_code == 200:
            return True
        elif response.status_code != 200:
            User.logger.debug(f"Could not register user: {response.status_code}")
        else:
            User.logger.debug(f"Could not register user: {response.json()['status']}")

        return False

    def validate(self, request):
        endpoint = User.api + "/user/validate"

        response = requests.post(endpoint, params = request.form.to_dict())

        if response.status_code == 200 and response.json()["status"] == "Validated":
            self._is_authenticated = True
            self._is_active = True
            return True
        elif response.status_code != 200:
            User.logger.debug(f"Could not validate user: {response.status_code}")
        else:
            User.logger.debug(f"Could not validate user: {response.json()['status']}")
        

        # Avoid abuse by malicious actors
        time.sleep(2)
        return False
    
    def update_password(self, request):
        endpoint = User.api + "/user/update"

        data = request.form.to_dict()
        data["username"] = self.id

        response = requests.post(endpoint, params = data)

        if response.status_code == 200 and "Updated" in response.json()["status"]:
            return True
        elif response.status_code != 200:
            User.logger.debug(f"Could not update user password: {response.status_code}")
        else:
            User.logger.debug(f"Could not update user password: {response.json()['status']}")
        
        return False
    
    def delete(self):
        endpoint = User.api + "/user/remove"

        response = requests.delete(endpoint, params = {"username": self.id})

        if response.status_code == 200:
            return True
        elif response.status_code != 200:
            User.logger.debug(f"Could not remove user: {response.status_code}")
        else:
            User.logger.debug(f"Could not remove user: {response.json()['status']}")
        
        return False
    
    def __str__(self) -> str:
        return f"<User ({self.id}, {self._exists}, {self._is_authenticated})>"
