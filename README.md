# Group 12 Semester project

## Sprint 2
See CS4320.Group.12.Semester.Project.-.Requirements.pdf in root directory

# augur_ML


Install Augur following 



Follow https://oss-augur.readthedocs.io/en/main/schema/regularly_used_data.html to get familiarize with message schema.

Export schema as csv.


Use csv in Sentimental Analysis using BERT.ipynb to perform sentimental analysis














# augur_view

HTML frontend for Chaoss/Augur, written with Bootstrap and served by Flask

## To run as a local development instance:

1. [setup a virtual environment](https://docs.python.org/3/library/venv.html#module-venv)
    - `python3 -m venv env`
    - `source env/bin/activate`
2. Make sure you have the requirements installed
    - `pip3 install -r requirements.txt`
3. Run the app
    - `./run.sh`

Once the server is running, you can change the default `serving` url in `config.yml` and either restart the app or navigate to `[approot]/settings/reload` in the browser to connect to the desired augur instance. For example, if you are serving from http://new.augurlabs.io you would enter the url: http://new.augurlabs.io/settings/reload.

## Quick start with Docker

Acquire the [Dockerfile](Dockerfile), and run the following commands in the terminal:
```bash
docker build -t augur-view .
```

```bash
docker run -p 8000:8000 augur-view
```

Note that the port configuration for the -p argument is `[host]:[container]`, in case you want to adjust the port mappings.

## Proxy and service installation

For installation instructions on a server, and information on setting up a proxy, see [installing](installing.md).

## Contributing

To get started with developing for augur_view, see [modules](modules.md).

Copyright 2021 University of Missouri, and University of Nebraska-Omaha
