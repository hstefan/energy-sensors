# Energy Sensors

A collection of services meant to receive, parse, and process telemetric data
from energy sensors.

The core service is *logservice*, which is responsible for receiving energy sensor data, as well
as exposing useful clustering statistics, calculated automatically by it on a separate worker
thread when a given event count is reached. Provides the following views:

- POST /log/store: saves sensor data based on the request data, interally incrementing the event
count on the worker thread and triggering clustering computation. Relies on HTTP status codes to
inform the client about the store result, returning either an empty JSON that will be empty for
sucessful queries, but contains a detailed error message in case of failure.
- GET /clusters/summary: returns a JSON representation of the calculated statistics for all cluster
data. Note that no elaborated computation is necessary for this request, as it relies on data that
was previously calculated by */log/store* and stored on the database.

An optional service called *parseservice* is also provided, which provides a single */log/parse*
view, that parses the POSTed data and returns a JSON representing that data. The idea of this
modularization is that */log/store* will bypass parsing the event to its internal dictionary if the 
*Content-Type* request header is set to *application/json*. Since the parsing is a pure and
stateless procedure, there can be as many instances of this service as needed, aiding scalability
by diverting the parsing load to this separate service.

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

The setup process was tested in a Linux environment, but it should still work with other systems
that support python (possibly with some shell adaptations).

## Running the Test Suite

*Note: assumes the virtualenv was correctly set-up and is currently active.*

```bash
nosetests tests/
```

Future work: improve coverability.

## Running the Services

*Note: assumes the virtualenv was correctly set-up and is currently active.*

```bash
# log service, binds to port 5000
./energy_sensors/logservice/logservice.py
```

```bash
# parse service, binds to port 5001 (optional)
./energy_sensors/parseservice/parseservice.py
```

## Running the Demo Automated Clients

*Note: assumes the virtualenv was correctly set-up and is currently active.*

```bash
# sends lines read from res/event.txt one-by-one to the log store service
./scripts/send_events.py "http://localhost:5000/log/store" res/events.txt

# sends pre-parsed data to /log/store by forwarding responses from /log/parse
/scripts/send_distributed_events.py "http://localhost:5001/log/parse" "http://localhost:5000/log/store" res/events.txt
```

If any of those scripts is ran at least once, *http://localhost:5000/clusters/summary* should
report the calculated attributes for each cluster, the input file contained at least 1000 rows.
