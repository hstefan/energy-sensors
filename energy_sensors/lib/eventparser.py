#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provides facilities for parsing a custom format."""

import re
import dateutil.parser

_RE_KNOWN_SUFFIXES = re.compile(r'^([+-]?\d+[\.|,]?\d*)(v|var|va|w|rad)?$', re.IGNORECASE)

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
            if not key or val is None:
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
    key, val_str = None, None
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
                val_str = string[val_start:idx]
            else:
                val_str = string[val_start:idx + 1]
            return (key, _decode_value(val_str), idx + 1)
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
                val_str = string[start:idx].strip()
            else:
                val_str = string[start:idx + 1].strip()
            start = idx + 1
            elements.append(_decode_value(val_str))
            # if at least one element is read, no further ':' are allowed inside array values
            list_term.add(':')
        idx += 1

    return (elements, start)

def _try_float_parse(value_str):
    """Tries to convert from string to float.
    Returns:
        float value if succesful, None otherwise."""
    value_str = _trim_known_suffixes(value_str).replace(',', '.')
    try:
        return float(value_str)
    except ValueError:
        return None

def _try_int_parse(value_str):
    """Tries to convert from string to int.
    Returns:
        int value if succesful, None otherwise."""
    value_str = _trim_known_suffixes(value_str)
    try:
        return int(value_str)
    except ValueError:
        return None

def _try_date_parse(value_str):
    """Tries to convert from string to datetime.
    Returns:
        datetime value if succesful, None otherwise."""
    try:
        return dateutil.parser.parse(value_str)
    except ValueError:
        return None

def _trim_known_suffixes(string):
    match = _RE_KNOWN_SUFFIXES.match(string)
    if match:
        return match.group(1)
    return string

def _decode_value(value_str):
    """Attempts to decode a string representation for the supported data types.
    Returns:
        Decoded type, otherwise the original string.
    """
    # attempt to match boolean patterns
    if value_str.lower() == 'off':
        return False
    elif value_str.lower() == 'on':
        return True
    # attempt to match int
    int_val = _try_int_parse(value_str)
    if int_val is not None:
        return int_val
    # attempt to match float
    float_val = _try_float_parse(value_str)
    if float_val is not None:
        return float_val
    # attempt to match datetime
    date_val = _try_date_parse(value_str)
    if date_val is not None:
        return date_val
    return value_str
