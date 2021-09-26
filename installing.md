# Running on a server
To run Augur-View headless on a server, we'll install it as a system service under systemd and proxy it through your web server of choice. The WSGI server will be run under Gunicorn for performance reasons. we'll provide proxy instructions for Apache and NGINX. These instructions assume you have a working web server (such as Apache or NGINX) already installed.

---

Make sure you have the proxy modules enabled in your web server. In Apache, this can be done with:

```
a2enmod
```

Then, provide the following list of modules at the prompt:
```
proxy proxy_ajp proxy_http rewrite deflate headers proxy_balancer proxy_connect proxy_html
```

## Preparing the app
In the root augur_view folder, create a new Python file, we'll call it `wsgi.py`, and populate it with the following code:

```
from augur_view import app

if __name__ == '__main__':
	app.run()
```

This will set up the flask server to run under Gunicorn as a service. Next, we need to create the service.

### Create a virtual environment

If you haven't already, you'll need to create a virtual environment to run the service. If you don't have virtualenv installed already, run

```
sudo apt-get install python3-venv
```

From the augur_view directory, run
```
python3 -m venv env
```

Then run `source env/bin/activate` to activate the virtual environment.

At this point, if you need to install flask and Gunicorn, run `pip install flask gunicorn`

## Installing the service

To install the service, create the following file at `/etc/systemd/system/augur_view.service`

```
[Unit]
Description=Gunicorn instance to serve augur_view flask application
After=network.target

[Service]
User=<user to run the service>
Group=<(optional) goup with permissions to access augur_view directory>
WorkingDirectory=<augur_view directory absolute path>
ExecStart=env/bin/gunicorn -c gunicorn.conf -b 0.0.0.0:8000 wsgi:app

[Install]
WantedBy=multi-user.target
```

We're using port `8000` here for the frontend.

Now create the `gunicorn.conf` file in the augur_view directory:

```
import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
bind = 'unix:AugurView.sock'
umask = 0o007
reload = True

#logging
accesslog = 'access.log'
errorlog = 'error.log'
```


## Proxy with Apache

To proxy with Apache, you need to edit an existing virtualhost or create a new one. The proxy you create should direct traffic to localhost, using the port you chose above (such as `8000`). You can replace the Location below with any relative address of your choice (such as "/").

If you are using the `000-default.conf` site file, you can edit the http virtualhost by appending the following proxy and location blocks to the end of the `*:80` entry:
```
    <Proxy *>
        Order deny,allow
        Allow from all
    </Proxy>
    ProxyPreserveHost On
    <Location "/augur">
          ProxyPass "http://127.0.0.1:8000/"
          ProxyPassReverse "http://127.0.0.1:8000/"
    </Location>
```
Remember to restart Apache after saving your changes. 

## Proxy with NGINX

To proxy with NGINX, you need to add a reverse proxy location to the NGINX config file your server is using. The location block should direct traffic to localhost, using the port you chose above (such as `8000`). You can replace the Location below with any relative address of your choice (such as "/").
```
location /augur {
    proxy_pass http://127.0.0.1:8000;
}
```
