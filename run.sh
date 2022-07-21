export CONFIG_LOCATION="config.yml"
export SERVER_ADDRESS="127.0.0.1"
export SERVER_PORT="8000"

# Notify the bootstrapper not to generate a Gunicorn config
# Also launch with the development server
export DEVELOPMENT=1

python3 bootstrap.py
