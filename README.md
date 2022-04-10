# augur_view

HTML frontend for Chaoss/Augur, written with Bootstrap and served by Flask

To run as a local instance:

1. setup a virtual environment
    - `python3 -m venv env`
    - `source env/bin/activate`
2. Make sure you have the requirements installed
    - `pip3 install python3-venv flask pyyaml urllib3`
3. Run the app
    - `./run.sh`

Once the server is running, you can change the default `serving` url in `config.yml` and either restart the app or navigate to `[approot]/settings/reload` in the browser to connect to the desired augur instance.

For installation instructions on a server, see [installing](installing.md).

## Deployed Server

1. [Backend](http://ec2-3-138-116-248.us-east-2.compute.amazonaws.com:5000/)
2. [Frontend](http://ec2-3-138-116-248.us-east-2.compute.amazonaws.com:8000/)

## Sprint 1

1. [Use Cases](use-cases.pdf)
2. [Requirements](requirements.pdf)
3. [Progress Report](progress-report.pdf)
4. [Obstacles & Reflections & Goals](obstacles-reflections-goals.pdf)

## Contributing

To get started with developing for augur_view, see [modules](modules.md).

Copyright 2021 University of Missouri, and University of Nebraska-Omaha
