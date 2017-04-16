#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the EventParser library."""

import energy_sensors.lib.eventparser as eventparser

def test_empty_string():
    """Checks nothing unexpected happens with empty input."""
    assert eventparser.parse_event_to_dict('') == {}

def test_orphan_attribute():
    """Checks if a string with an orphan attribute would return an empty dict."""
    assert eventparser.parse_event_to_dict('Dead=Beef') == {}

def test_array_root():
    """Checks if a top-level array string would return an empty dict."""
    assert eventparser.parse_event_to_dict('A; B; C;') == {}

def test_empty_object():
    """Checks that empty objects return the expected dictionary."""
    assert eventparser.parse_event_to_dict('Foo:') == {'Foo' : {}}

def test_object_array():
    """Checks if arrays are correctly parsed."""
    assert eventparser.parse_event_to_dict('Foo: 1; 2; 3;') == {'Foo' : ['1', '2', '3']}

def test_object_key():
    """Checks if key-based values are correctly parsed."""
    assert eventparser.parse_event_to_dict('Foo: Bar=Baz;') == {'Foo' : {'Bar': ['Baz']}}

def test_object_key_array():
    """Checks if key-based arrays are correctly parsed;"""
    assert eventparser.parse_event_to_dict('Foo: Bar=A;B;C;') == {'Foo' : {'Bar': ['A', 'B', 'C']}}

def test_mutiple_objects():
    """Checks if multiple objects arrays are correctly parsed;"""
    event_dict = eventparser.parse_event_to_dict('Foo: Bar=A; Baz: Attr=B;')
    assert event_dict == {'Foo' : {'Bar': ['A']}, 'Baz': {'Attr': ['B']}}

def test_mutiple_arrays_sections():
    """Checks if multiple array sections are correctly parsed."""
    event_dict = eventparser.parse_event_to_dict('Foo: A; B; C; Bar: X; Y; Z;')
    assert event_dict == {'Foo' : ['A', 'B', 'C'], 'Bar': ['X', 'Y', 'Z']}

if __name__ == '__main__':
    test_empty_string()
