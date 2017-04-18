#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the EventParser library."""

import energy_sensors.lib.eventparser as eventparser
from nose.tools import raises

def test_empty_string():
    """Checks nothing unexpected happens with empty input."""
    assert eventparser.parse_event_to_dict('') == {}

def test_orphan_attribute():
    """Checks if a string with an orphan attribute would return an empty dict."""
    assert eventparser.parse_event_to_dict('Dead=Beef') == {}

def test_array_root():
    """Checks if a top-level array string would return an empty dict."""
    assert eventparser.parse_event_to_dict('A; B; C;') == {}

@raises(eventparser.EventParseError)
def test_empty_object():
    """Checks that empty objects return the expected dictionary."""
    eventparser.parse_event_to_dict('Foo:')

def test_object_array():
    """Checks if arrays are correctly parsed."""
    assert eventparser.parse_event_to_dict('Foo: 1; 2; 3;') == {'Foo' : ['1', '2', '3']}

def test_object_key():
    """Checks if key-based values are correctly parsed."""
    assert eventparser.parse_event_to_dict('Foo: Bar=Baz;') == {'Foo' : {'Bar': 'Baz'}}

def test_object_key_array():
    """Checks if key-based arrays ignore invalid elements."""
    event_dict = eventparser.parse_event_to_dict('Foo: Bar=A;B;C;')
    assert event_dict == {'Foo': {'Bar': 'A'}}

def test_mutiple_objects():
    """Checks if multiple objects arrays are correctly parsed;"""
    event_dict = eventparser.parse_event_to_dict('Foo: Bar=A; Baz: Attr=B;')
    assert event_dict == {'Foo' : {'Bar': 'A'}, 'Baz': {'Attr': 'B'}}

def test_mutiple_arrays_sections():
    """Checks if multiple array sections are correctly parsed."""
    event_dict = eventparser.parse_event_to_dict('Foo: A; B; C; Bar: X; Y; Z;')
    assert event_dict == {'Foo' : ['A', 'B', 'C'], 'Bar': ['X', 'Y', 'Z']}

def test_attribute_datetime_parsing():
    """Checks if date-like attributes are parsed correctly."""
    event_dict = eventparser.parse_event_to_dict('Datetime: 2016-10-4 16:47:50;')
    assert event_dict == {'Datetime' : ['2016-10-4 16:47:50']}

def test_array_end_no_semicolon():
    """Tests if arrays with no semicolon on the end are parsed correctly."""
    event_dict = eventparser.parse_event_to_dict('Foo: A; B')
    assert event_dict == {'Foo': ['A', 'B']}

def test_key_value_end_no_semicolon():
    """Test if key-value sections with no ending semicolon are parsed correctly."""
    event_dict = eventparser.parse_event_to_dict('Foo: A=0; B=1')
    assert event_dict == {'Foo':{'A': '0', 'B': '1'}}

@raises(eventparser.EventParseError)
def test_semicolon_in_value():
    """Tests if key-value pairs containing semicolons cause a parse error."""
    eventparser.parse_event_to_dict('Foo: Bar=:')
