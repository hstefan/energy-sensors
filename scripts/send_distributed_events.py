#!/usr/bin/env python

import requests
import sys

parse_url = sys.argv[1]
store_url = sys.argv[2]
input_file = sys.argv[3]

with open(input_file) as events_file:
    for event_str in events_file:
        payload = requests.post(parse_url, data=event_str).content.decode('utf-8')
        requests.post(store_url, json=payload)
