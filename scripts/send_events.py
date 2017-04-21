#!/usr/bin/env python

import requests
import sys

store_url = sys.argv[1]
input_file = sys.argv[2]
with open(input_file) as events_file:
    for event_str in events_file:
        requests.post(store_url, data=event_str, headers={'Content-Type':'text/plain'})

