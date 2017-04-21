#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A web-service that stores and allows querying of energy sensor events."""

from flask import Flask, request
import energy_sensors.lib.eventparser as eventparser
from energy_sensors.logservice.db import Cluster, EventLog, get_db_sessionmaker
from energy_sensors.logservice.clustering import ClusteringBatchWorker
from energy_sensors.lib.responseutils import json_error_response, json_response

app = Flask(__name__)
# this should really be a separate process for the optimal performance
clustering_worker = ClusteringBatchWorker(1000)

@app.route('/log/store', methods=['POST'])
def log_store():
    """Parses data POSTed and logs to the database."""
    # validates content-type
    content_type = request.headers.get('Content-Type', None)
    event_dict = None
    json_mime = 'application/json'
    text_mime = 'text/plain'

    if content_type == text_mime:
        # parse data before attempting to store
        data_str = request.data.decode('utf-8')
        event_dict = eventparser.parse_event_to_dict(data_str)
        if not event_dict:
            return json_error_response('Failed to parse event text.')

    if content_type == json_mime:
        # bypass all the parsing and extract json from POST data
        event_dict = request.json()
        if not event_dict:
            # possibly invalid json syntax or a general decoding failure
            return json_error_response('Failed to decode json payload.')

    if event_dict is None:
        # if we reach here, no handler was found
        return json_error_response('Unable to decode content-type "{}".'.format(content_type))

    log_entry = EventLog.from_event_dict(event_dict)
    if not log_entry:
        return json_error_response('Unabled to extract all fields from the given data.')

    session = get_db_sessionmaker(debug=True)()
    session.add(log_entry)
    session.commit()

    clustering_worker.report_event_received()

    # returns an empty json, also indicading success via http status code
    return json_response({})

@app.route('/clusters/summary', methods=['GET'])
def clusters_summary():
    """Generates a json report with data on current clusters."""
    session = get_db_sessionmaker(debug=True)()
    clusters = session.query(Cluster).all()
    summary_dict = {'clusters' : [c.to_dict() for c in clusters]}
    return json_response(summary_dict)

if __name__ == '__main__':
    app.run()
