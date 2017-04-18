#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database models and utilities for energy_sensors.logservice functionalities."""

from sqlalchemy import Boolean, BigInteger, Column, Float, Integer, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

BASE = declarative_base()

class EventLog(BASE):
    """
    Flat model meant to store entries parsed from the custom event format.
    All fields are stored in the database, even though some would not be necessarily be used by
    the logservice. This choice was made to favor completeness and future-proofing.

    Attributes:
        id                  Automatically generated primary key for the table.
        log_time_utc        The UTC timestamp for when a given entry was stored.
        device_id           Reported integer id of the reporting device.
        reported_time_utc   The UTC timestamp reported by then event entry, not necessarily the
                            same as log_time_utc.
        coil_reversed       Boolean representing alarm coil state.
        power_active_w      Active power in Watts.
        power_reactive_var  Reactive power in volt-ampere reactive.
        power_apparent_va   Apparent power in volt-ampere.
        line_current_a      Current of the power line in ampere.
        line_voltage_v      Voltage of the power line in volts.
        line_phase_rad      Phase of the power line in radians.
        line_frequency      AC frequency of the power line in hertz.
        line_peaks          Semicolon-separated values for transients/peaks.
                            e.g: 10.5459;10.5;10.553
        fft_harmonics       Semicolon-separated tuples for harmonics calculated with FFT.
                            The tuples are in the (real,imaginary) format, representing complex
                            numbers.
                            eg: 1083,2131;778.12,184.69;244.42,-844
        wifi_strength_dbm   Measured strength of wifi signal in decibel-milliwatts.
        dummy_data          Unspecified placeholder data.
    """

    __tablename__ = 'events'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    log_time_utc = Column(TIMESTAMP, nullable=False, server_default='current_timestamp')
    device_id = Column(Integer, nullable=False)
    device_fw = Column(Integer, nullable=False)
    reported_time_utc = Column(TIMESTAMP, nullable=False)
    coil_reversed = Column(Boolean, nullable=False)
    power_active_w = Column(Float, nullable=False)
    power_reactive_var = Column(Float, nullable=False)
    power_apparent_va = Column(Float, nullable=False)
    line_current_a = Column(Float, nullable=False)
    line_voltage_v = Column(Float, nullable=False)
    line_phase_rad = Column(Float, nullable=False)
    line_frequency = Column(Float, nullable=False)
    current_peaks_list = Column(Text, nullable=False)
    fft_harmonics = Column(Text, nullable=False)
    wifi_strength_dbm = Column(Text, nullable=False)
    # NOTE: do we need to really store this, or is it just an artifact?
    dummy_data = Column(Integer, nullable=False)
