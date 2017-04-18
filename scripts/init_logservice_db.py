#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initializes an SQLite database for the logservice.
"""

import energy_sensors.logservice.db
from sqlalchemy import create_engine

ENGINE = create_engine('sqlite:///logservice.db', echo=True)
energy_sensors.logservice.db.BASE.metadata.create_all(ENGINE)
