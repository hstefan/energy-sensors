# Sensor Data Provider

A collection of services meant to receive, parse, and process telemetric data
from power sensors.

The setup process was tested in a Linux environment, but it should still work with other systems
that support python (possibly with some shell adaptations).

## Development and Testing Setup

```bash
#create virtualenv
python3 -m venv venv
source venv/bin/activate
# install dependencies
pip install -r dev-requirements.txt
pip install -e .
# initializes databases
./scripts/init_logservice_db.py
```

## Running the Test Suite

```bash
nosetests tests/
```
