from werkzeug.serving import make_server
from werkzeug.debug import DebuggedApplication
import threading, os

class Environment:
    """
    This class is used to make dealing with environment variables easier. It
    allows you to set multiple environment variables at once, and to get items
    with subscript notation without needing to deal with the particularities of
    non-existent values.
    """
    def __init__(self, **kwargs):
        for (key, value) in kwargs.items():
            self[key] = value

    def setdefault(self, key, value):
        if not self[key]:
            self[key] = value
            return value
        return self[key]

    def setall(self, **kwargs):
        result = {}
        for (key, value) in kwargs.items():
            if self[key]:
                result[key] = self[key]
            self[key] = value

    def getany(self, *args):
        result = {}
        for arg in args:
            if self[arg]:
                result[arg] = self[arg]
        return result

    def as_type(self, type, key):
        if self[key]:
            return type(self[key])
        return None

    def __getitem__(self, key):
        return os.getenv(key)

    def __setitem__(self, key, value):
        os.environ[key] = str(value)

    def __len__(self)-> int:
        return len(os.environ)

    def __str__(self)-> str:
        return str(os.environ)

    def __iter__(self):
        return (item for item in os.environ.items)

class ServerThread(threading.Thread):
    """
    Create a runnable Flask server app that automatically launches on a separate
    thread.
    """
    def __init__(self, app, port = 5000, address = "0.0.0.0", reraise = False):
        threading.Thread.__init__(self)

        # Required to enable debugging with make_server
        app.config['PROPAGATE_EXCEPTIONS'] = reraise
        debug_app = DebuggedApplication(app, True)

        self.server = make_server(address, port, debug_app, threaded = True)
        self.ctx = app.app_context()
        self.ctx.push()

        # For compatibility with subprocesses
        self.terminate = self.shutdown
        self.wait = self.join

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
