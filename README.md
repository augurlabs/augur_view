# Sprint 3
See [write up](4320 Semester Project - Sprint 3.pdf) for more information!


# Sprint 2
See [write up](4320 Semester Project - Sprint 2.pdf) for more information!

# augur_view

HTML frontend for Chaoss/Augur, written with Bootstrap and served by Flask

To run as a local instance:

1. setup a virtual environment
    - `python3 -m venv env`
    - `source env/bin/activate`
2. Make sure you have the requirements installed
    - `pip3 install flask pyyaml urllib3`
3. Run the app
    - `./run.sh`
4. Open up the webpage at either
    - `localhost:5000/status`
    - `127.0.0.1:5000/status`

Once the server is running, you can change the default `serving` url in `config.yml` and either restart the app or navigate to `[approot]/settings/reload` in the browser to connect to the desired augur instance.

For installation instructions on a server, see [installing](installing.md).

## Contributing

To get started with developing for augur_view, see [modules](modules.md).

Copyright 2021 University of Missouri, and University of Nebraska-Omaha
