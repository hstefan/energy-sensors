#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provides facilities for parsing a custom format."""

class EventParseError(Exception):
    pass

def parse_event_to_dict(event_entry):
    """Returns a hierarchy of dictionaries containing attributes extracted from event_entry."""
    objs = {}
    idx = 0
    while idx < len(event_entry):
        section, idx = _read_section(event_entry, idx)
        if not section:
            break
        objs[section] = {}

        # attempt to parse array of elements
        attr_values, idx = _read_array_elements(event_entry, idx)
        if attr_values:
            objs[section] = attr_values
            continue

        # attempt to parse key-value pairs
        while idx < len(event_entry):
            key, val, idx = _read_key_value(event_entry, idx)
            if not key or not val:
                break
            objs[section][key] = val

        if not objs[section]:
            raise EventParseError('Expected either a list of key-value pairs or list of elements.')
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
            # semicolons are not allowed in a section declarion
            break
        if string[idx] == ':':
            # colons are the final delimiter for a section
            section = string[start:idx].strip()
            return (section, idx + 1)
        idx += 1
    return (None, start)

def _read_key_value(string, start):
    start = _skip_whitespaces(string, start)
    idx = start
    key, value = None, None
    str_len = len(string)
    # a valid key attribute wouldn't contain any ':', but instead a non-empty
    # sequence ending with '='
    while not key and idx < str_len:
        curr_ch = string[idx]
        if curr_ch == ':':
            break
        if curr_ch == '=':
            key = string[start:idx].lstrip()
        idx += 1

    if not key:
        # beginning of key-value pattern wasn't found
        return (None, None, start)

    val_start = _skip_whitespaces(string, idx)
    idx = val_start
    while idx < str_len:
        curr_ch = string[idx]
        if curr_ch == ':':
            # no ':' character is allowed in a value
            break
        if curr_ch == ';' or idx == str_len - 1:
            # the value would be valid if either the end of the string is reached, or a ';' char
            if curr_ch == ';':
                value = string[val_start:idx]
            else:
                value = string[val_start:idx + 1]
            return (key, value, idx + 1)
        idx += 1

    return (None, None, start)

def _read_array_elements(string, start):
    start = _skip_whitespaces(string, start)
    idx = start
    elements = []
    # list of symbols that would terminate a value enumeration
    list_term = {'='}

    str_len = len(string)
    while idx < str_len:
        curr_ch = string[idx]

        if curr_ch in list_term:
            break

        if curr_ch == ';' or idx == str_len - 1:
            # an array item is either the end is reached or a ';' char is found
            if curr_ch == ';':
                val = string[start:idx].strip()
            else:
                val = string[start:idx + 1].strip()
            start = idx + 1
            elements.append(val)
            # if at least one element is read, no further ':' are allowed inside array values
            list_term.add(':')
        idx += 1

    return (elements, start)
