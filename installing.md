# Running on a server
To run Augur-View headless on a server, we'll install it as a system service under systemd and proxy it through your web server of choice. The WSGI server will be run under Gunicorn for performance reasons. we'll provide proxy instructions for Apache and NGINX. These instructions assume you have a working web server (such as Apache or NGINX) already installed.

---

Make sure you have the proxy modules enabled in your web server. With NGINX, proxy will already be enabled, but in Apache, this can be done with:

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

#### Installing requirements

Once you have your virtual environment created and activated, make sure you have the requirements installed
```
pip install -r requirements.txt 
```

## Installing the service

To install the service, create the following file at `/etc/systemd/system/augur_view.service`

You'll need to modify the file to your environment parameters.
- The `User` parameter defines the user which will be used to run the service. This can be your user account, the root user (not recommended), or a new user you create specifically for this app.
- The `Group` parameter optionally specifies the group to run the process as. It's not required for operation.
- The `WorkingDirectory` parameter describes where the service working directory is. This parameter should be set to the root directory where the `augur_view` executables are located.
- The `ExecStart` parameter describes the program to run when the service is started. For `augur_view`, we want Gunicorn to run on startup. In this instance, we need to break up this parameter into multiple parts:
    - First, we need the absolute or relative (to the `WorkingDirectory`) path to the Gunicorn executable. In this case, because our virtual environment is in the `augur_view` root directory, we are using the relative path to the executable.
    - Second, using the `-c` option, we specify the Gunicorn config file (which we demonstrate creating below), using its absolute or relative path.
    - Third, using the `-b` option, we specify the address for Gunicorn to bind to. In this case, we are using the local loopback address at port `8000`.
    - Finally, we specify the wsgi driver module we created earlier in `wsgi.py`, using its absolute or relative path.

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

Now create the `gunicorn.conf` file in the augur_view directory. You probably don't need to adjust any of the parameters in this file, but you may wish to specify different paths for the log files:

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
### Starting the service

To start the service, you need to run `sudo systemctl start augur_view` (or whatever you called your service file).

If you want the service to run on startup, you can run `sudo systemctl enable augur_view`.

## Proxy with Apache

To proxy with Apache, you need to edit an existing virtualhost or create a new one. The proxy you create should direct traffic to localhost, using the port you chose above (such as `8000`). You can replace the Location below with any relative address of your choice (such as "/augur").

If you are using the `000-default.conf` site file, you can edit the http virtualhost by appending the following proxy and location blocks to the end of the `*:80` entry:
```
    <Proxy *>
        Order deny,allow
        Allow from all
    </Proxy>
    ProxyPreserveHost On
    <Location "/">
          ProxyPass "http://127.0.0.1:8000/"
          ProxyPassReverse "http://127.0.0.1:8000/"
    </Location>
```
Remember to restart Apache after saving your changes.

## Proxy with NGINX

To proxy with NGINX, you need to add a reverse proxy location to the NGINX config file your server is using. The location block should direct traffic to localhost, using the port you chose above (such as `8000`). You can replace the Location below with any relative address of your choice (such as "/augur").

You will also need a running augur instance from https://github.com/chaoss/augur

The Server port will be used to proxy the API served by that instance, which is required by augur\_view.

`server_name` is the full domain that you will have augur\_view resolving to. 

`proxy_pass` for `location /api/unstable/` is the full domain that you have augur\_view resolving to, with an additional port specification that matches the server port specification in your running instance of augur.

**Create this file where your operating system keeps its `sites-enabled` directory. On Ubuntu, that is `/etc/nginx/sites-enabled`.** 

**After adding this file, execute `sudo nginx -t` to make sure it is configured correctly, and `sudo systemctl restart nginx` to have it take effect immediately** 

```
server {
        listen 80;
        server_name  new.augurlabs.io;

        location /api/unstable/ {
                proxy_pass http://new.augurlabs.io:5044;
                proxy_set_header Host $host;
        }

	location / {
		proxy_pass http://127.0.0.1:8000;
	}

        error_log /var/log/nginx/census.osshealth.error.log;
        access_log /var/log/nginx/census.osshealth.access.log;

}

```
### Note
Whatever location you set your proxy to, you'll need to update the `approot` parameter of the default config. The default `approot` is `"/"`.
