#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provides facilities for parsing a custom format."""

def parse_event_to_dict(event_entry):
    """Returns a hierarchy of dictionaries containing attributes extracted from event_entry."""
    objs = {}
    idx = 0
    while idx < len(event_entry):
        section, idx = _read_section(event_entry, idx)
        if not section:
            break
        objs[section] = {}
        while idx < len(event_entry):
            attribute, idx = _read_attribute(event_entry, idx)
            attr_values = []
            while idx < len(event_entry):
                attr_value, idx = _read_attribute_value(event_entry, idx)
                if not attr_value:
                    break
                else:
                    attr_values.append(attr_value)
            if not attribute and not attr_values:
                # we read neither attributes or a "array list", read next section
                break
            if attribute:
                objs[section][attribute] = attr_values
            else:
                # object is only a list of values, store and read next identifier
                objs[section] = attr_values
                break
    return objs

def _skip_whitespaces(string, start):
    while start < len(string) and string[start] == ' ':
        start += 1
    return start

def _read_section(string, start):
    start = _skip_whitespaces(string, start)
    idx = start
    while idx < len(string):
        if string[idx] == ';':
            break
        if string[idx] == ':':
            section = string[start:idx].strip()
            return (section, idx + 1)
        idx += 1
    return (None, start)

def _read_attribute(string, start):
    start = _skip_whitespaces(string, start)
    idx = start
    while idx < len(string):
        if string[idx] in [':', ';']:
            break
        if string[idx] == '=':
            attribute = string[start:idx].strip()
            return (attribute, idx + 1)
        idx += 1
    return (None, start)

def _read_attribute_value(string, start):
    start = _skip_whitespaces(string, start)
    idx = start
    while idx < len(string):
        if string[idx] in [':', '=']:
            break
        if string[idx] == ';':
            val = string[start:idx].strip()
            return (val, idx + 1)
        idx += 1
    return (None, start)
