from flask_login import UserMixin
from init import hash_algorithm, users_db
import sqlite3, time

""" ----------------------------------------------------------------
"""
class User(UserMixin):
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

    def _read_db(self):
        cursor = sqlite3.connect(users_db).cursor()
        cursor.execute("SELECT * FROM users WHERE user_id=:id", {"id": self.id})
        result = cursor.fetchall()

        if len(result) == 1:
            self.data = result[0]
            self._is_active = bool(result[0][2])

    def __init__(self, id):
        # flask_login requires that the id be of type string
        self.id = str(id)
        self._is_anonymous = False
        self._is_authenticated = False
        self._is_active = False

        self._read_db()

    def get_id(self):
        return self.id

    def exists(self):
        return hasattr(self, "data")

    def register(self, password):
        if self.exists():
            return False

        connection = sqlite3.connect(users_db)
        cursor = connection.cursor()

        hashing = hash_algorithm()
        hashing.update(password.encode('utf8'))
        pass_hash = hashing.hexdigest()
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (self.id, pass_hash, 1))
        connection.commit()

        self._read_db()
        return True

    def validate(self, password):
        if self.exists():
            hashing = hash_algorithm()
            hashing.update(password.encode('utf8'))
            pass_hash = hashing.hexdigest()
            if pass_hash == self.data[1]:
                self._is_authenticated = True
                return True

        # Avoid abuse by malicious actors
        time.sleep(2)
        return False
