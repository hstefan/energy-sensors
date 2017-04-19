#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A web-service that stores and allows querying of energy sensor events."""

from http import HTTPStatus
from flask import Flask, request, jsonify
import flask.json
import energy_sensors.lib.eventparser as eventparser
from energy_sensors.logservice.db import EventLog, get_db_session

app = Flask(__name__)

def json_response(json_dict, http_status=HTTPStatus.OK):
    resp = jsonify(json_dict)
    resp.status_code = http_status.value
    return resp

def json_error_response(error, http_status=HTTPStatus.BAD_REQUEST):
    return json_response({'error': error}, http_status)

@app.route('/log/store', methods=['POST'])
def log_store():
    """Parses data POSTed and logs to the database."""
    # validates content-type
    content_type = request.headers.get('Content-Type', None)
    if content_type != 'application/json':
        return json_error_response('Unsupported content type.')

    data_json = flask.json.loads(request.data)
    if not data_json:
        return json_error_response('Unable do parse json from POST data.')

    event_str = data_json.get('entry', None)
    if not event_str:
        return json_error_response('Missing value on json data.')

    parsed_event = eventparser.parse_event_to_dict(event_str)
    if not parsed_event:
        return json_error_response('Failed to parse event.')

    log_entry = EventLog.from_event_dict(parsed_event)
    if not log_entry:
        return json_error_response('Unabled to extract all fields from the given data.')

    db_session = get_db_session(debug=True)
    db_session.add(log_entry)
    db_session.commit()

    return json_response(parsed_event)

if __name__ == '__main__':
    app.run()
