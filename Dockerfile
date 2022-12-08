FROM python:3.8

# -------- Set up environment and variables --------

# Tell the bootstrapper that we're working from Docker
ENV IS_DOCKER=1

# CONFIGURATION should eventually support any of <file, database, url, redis>
# At the moment, only ["file"] is supported
ENV CONFIGURATION=file

# CONFIG_LOCATION defaults to config_temp.yml, you can change it like so:
# ENV CONFIG_LOCATION=config.yml

# The Gunicorn port defaults to 8000
EXPOSE 8000

# You can specify an alternate Gunicorn port with
# ENV SERVER_PORT=5000

# You can run the server in development mode with
# ENV DEVELOPMENT=1

# -------- Configure application --------

# Clone the augur_view source and set the new folder as the working directory
RUN git clone -b dev https://https://github.com/Simon-SS/augur_view_group_12.git app
WORKDIR /app

# Since we specified CONFIGURATION=file above, we provide it here
# If a file is not provided, first-time setup will run on each startup
# COPY config.yml ./

RUN pip install -r requirements.txt

CMD ["python", "bootstrap.py"]
