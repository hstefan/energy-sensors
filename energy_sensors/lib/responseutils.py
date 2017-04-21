#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""""Provides convenient functions for flask and json interactions."""

from http import HTTPStatus
from flask import jsonify

def json_response(json_dict, http_status=HTTPStatus.OK):
    """Creates a json response object with the specified http status."""
    resp = jsonify(json_dict)
    resp.status_code = http_status.value
    return resp

def json_error_response(error, http_status=HTTPStatus.BAD_REQUEST):
    """Creates a standardized error representation with the specified https status."""
    return json_response({'error': error}, http_status)
