#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provides one single function to parse our custom event format to a json representation."""

from flask import Flask, request
import energy_sensors.lib.eventparser as eventparser
from energy_sensors.lib.responseutils import json_error_response, json_response

app = Flask(__name__)

@app.route('/log/parse', methods=['POST'])
def log_parse():
    content_type = request.headers.get('Content-Type', None)
    event_dict = None
    allowed_mime_types = ['text/plain']

    if content_type not in allowed_mime_types:
        return json_error_response('Unsupported content-type: "{}"', content_type)

    # decode post data and parse
    data_str = request.data.decode('utf-8')
    event_dict = eventparser.parse_event_to_dict(data_str)
    if not event_dict:
        return json_error_response('Failed to parse event text.')

    # returns the parsed dictionary (also valid JSON)
    return json_response(event_dict)

if __name__ == '__main__':
    # port is 5001 to ease testing (avoid bind conflict with logservice, for instance)
    app.run(port=5001)
