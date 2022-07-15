from pathlib import Path
from server import Environment
import os, yaml, subprocess

gunicorn_conf = """import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
bind = 'unix:AugurView.sock'
umask = 0o007
reload = True

#logging
accesslog = 'access.log'
errorlog = 'error.log'
"""

def first_time(port):
    """
    Run first time setup for this instance.
    """
    from flask import Flask, request, render_template
    from init import settings, init_settings
    from server import ServerThread
    import threading

    init_settings()

    # Not all of the settings are editable (such as 'version' or 'session_key')
    sections = [
        { "title": "File System", "settings": [
            { "id": "caching",
                "display_name": "Cache Directory",
                "value": settings["caching"],
                "description": "Folder path for storing cache files"
            },{ "id": "cache_expiry",
                "display_name": "Cache Expiration",
                "value": settings["cache_expiry"],
                "description": "Time (in seconds) before cache files expire"
            },{ "id": "reports",
                "display_name": "Reports File",
                "value": settings["reports"],
                "description": "The configuration file which stores the description for the report page"
            }
        ]},
        { "title": "Network", "settings": [
            { "id": "serving",
                "display_name": "Augur API URL",
                "value": settings["serving"],
                "description": "The Augur API url to use for requests"
            },{ "id": "approot",
                "display_name": "Application Root",
                "value": settings["approot"],
                "description": "The url path for the root of this application"
            }
        ]}
    ]

    app = Flask(__name__)

    def all_in(source, update):
        for key in update.keys():
            if key not in source:
                return False
        return True

    # Create a multithreading context for message passing
    update_complete = threading.Condition()

    @app.route("/")
    def root():
        return render_template("first-time.html", sections = sections, gunicorn_placeholder = gunicorn_conf, version = settings.get("version"))

    @app.route("/update", methods=['POST'])
    def update_config():
        try:
            new_config = request.get_json()
            # Check that the new config has valid keys
            if all_in(settings, new_config):
                settings.update(new_config)
            else:
                # The form submitted contains a key not in the settings dict
                raise ValueError(f"A form error occurred: {new_config}")
        except Exception as e:
            # Indicate that an error occurred
            # Return for flashing to the user in a modal dialog
            return str(e), 500

        # The first-time setup page should just redirect to /stop on success
        return settings.get("approot")

    @app.route("/gunicorn", methods=['POST'])
    def update_gunicorn():
        global gunicorn_conf
        gunicorn_conf = request.get_data(as_text = True)
        return ""

    @app.route("/stop")
    def shutdown():
        # Notify the primary thread that the temp server is going down
        update_complete.acquire()
        update_complete.notify_all()
        update_complete.release()
        return "Server shutting down"

    # Start a single-use server for first-time setup
    server = ServerThread(app, port = port, reraise = True)
    server.start()

    # Listen for the server /stop command, then shutdown the server
    update_complete.acquire()
    try:
        update_complete.wait()
    except KeyboardInterrupt as e:
        # Shutdown gracefully on interrupt and abort relaunch
        settings = None
    except Exception as e:
        # On an unexpected exception, reraise after shutting down
        raise e
    finally:
        server.shutdown()
        update_complete.release()

    return settings

if __name__ == "__main__":
    env = Environment()
    config_methods = ['file']
    config = os.getenv("CONFIGURATION")

    if config is None:
        config = "file"
    elif config not in config_methods:
        raise NotImplementedError(f"The CONFIGURATION method specified must be one of: {config_methods}")

    config_location = Path(env.setdefault("CONFIG_LOCATION", "config_temp.yml"))
    gunicorn_location = Path(env.setdefault("GUNICORN_CONFIG", "gunicorn_temp.py"))
    host_address = env.setdefault("SERVER_ADDRESS", "0.0.0.0")
    server_port = int(env.setdefault("SERVER_PORT", 8000))

    if not config_location.is_file():
        settings = first_time(server_port)

        if not settings:
            # First time setup was aborted, so just quit
            os._exit(1)

        with open(config_location, "w") as config_file:
            yaml.dump(settings, config_file)

    if not gunicorn_location.is_file():
        with open(gunicorn_location, "w") as gunicorn_py:
            gunicorn_py.write(gunicorn_conf)

    server = subprocess.Popen(["gunicorn", "-c", str(gunicorn_location), "-b", f"{host_address}:{server_port}", "augur_view:app"])

    try:
        server.wait()
    except KeyboardInterrupt:
        # Shutdown gracefully on interrupt
        server.terminate()

    # os.getenv("IS_DOCKER")
