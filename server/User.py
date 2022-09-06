from flask_login import UserMixin
# I'm using requests here to avoid circular integration with utils
import requests, time

""" ----------------------------------------------------------------
"""
class User(UserMixin):
    # User.api is set in utils.py

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

    def register(self, request):
        endpoint = User.api + "/user/create"

        # TODO Sanitize data (IE: any rando could exploit this to create an admin account)
        response = requests.post(endpoint, params = request.form.to_dict())

        if response.status_code == 200:
            return True

        return False

    def validate(self, request):
        endpoint = User.api + "/user/validate"

        response = requests.post(endpoint, params = request.form.to_dict())

        if response.status_code == 200 and response.json()["status"] == "Validated":
            self._is_authenticated = True
            self._is_active = True
            return True

        # Avoid abuse by malicious actors
        time.sleep(2)
        return False
    
    def __str__(self) -> str:
        return f"<User ({self.id}, {self._exists}, {self._is_authenticated})>"
