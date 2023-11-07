# Howler API

This repo contains the API server for Howler

## Installation instructions

### Dependencies

In order to run howler, you need:

- Python 3.9
- Docker
- Docker Compose
- Recommended: Visual Studio Code

### Setup Howler Folders

```bash
sudo mkdir -p /etc/howler/conf
sudo mkdir -p /var/cache/howler
sudo mkdir -p /var/lib/howler
sudo mkdir -p /var/log/howler

sudo chown -R $USER /etc/howler
sudo chown $USER /var/cache/howler
sudo chown $USER /var/lib/howler
sudo chown $USER /var/log/howler
```

### Setup APT dependencies

```bash
sudo apt update
sudo apt install -yy software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -yy python3-venv python3.9 python3.9-dev python3.9-venv
sudo apt install -yy libsasl2-2 build-essential libsasl2-dev libssl-dev zip
```

### Create your virtualenv

```bash
cd ~/repos/howler-api
python3.9 -m venv env
. env/bin/activate
pip install -U pip
pip install -U wheel
pip install python-dotenv
pip install -e .
```

### Setup default configuration files

Create default classification.yml and config.yml files:

```bash
. env/bin/activate
./generate_howler_conf.sh
```

## Setup default environment

```bash
    cd ~/repos/howler-api
    echo "EXTERNAL_IP=`hostname -I | awk '{print $1}'`" > dev/.env
```

## Running development environment (VS Code)

Now that the installation instructions are completed, you can now load your `howler-api` folder. We strongly advise installing the recommended extensions when prompted or typing '@recommended' in the Extensions tab.

### Launch dependency containers

You can run the dependency containers either manually in a shell:

```bash
(cd ~/repos/howler-api/dev && docker-compose up)
```

Or directly in VSCode using the tasks in Task Explorer

![Task explorer](tasks.png)

### Launch the API

Once the dependencies are launched, you can start the API Server. The API server will be loaded with the default configuration found in your `/etc/howler/conf` folder that we've created during the setup. So if you want to enable/disable feature, do it there.

To launch the API server manually you can use this command:

```bash
cd ~/repos/howler-api
. env/bin/activate
python howler/app.py
```

Launching the API Server manually unfortunately does not give you access to a debugger. If you want to be able to debug you code, you can use the predefined launch target inside of VSCode:

![Task explorer](run_debug.png)

## Running Tests

In order to run the tests, start up the dependencies and launch the API, then use pytest:

```bash
# Install test dependencies
pip install -r test/requirements.txt

# Generate mitre lookups
python howler/external/generate_mitre.py /etc/howler/lookups

pytest -s -v
```
