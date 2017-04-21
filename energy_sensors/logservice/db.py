#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database models and utilities for energy_sensors.logservice functionalities."""

import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, Text, TIMESTAMP
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
        device_id           Integer id of the device.
        device_fw           Firmware version of the device.
        device_evt          Event type of the device.
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
                            eg: 1083,2131;778.12,184.69;244.42,-844;
        wifi_strength_dbm   Measured strength of wifi signal in decibel-milliwatts.
        dummy_data          Unspecified placeholder data.
    """

    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_time_utc = Column(TIMESTAMP, nullable=False, default=datetime.datetime.utcnow)
    device_id = Column(Integer, nullable=False)
    device_fw = Column(Integer, nullable=False)
    device_evt = Column(Integer, nullable=False)
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
    wifi_strength_dbm = Column(Float, nullable=False)
    # NOTE: do we need to really store this, or is it just an artifact?
    dummy_data = Column(Integer, nullable=False)

    @staticmethod
    def from_event_dict(event_dict):
        try:
            # TODO: type validation!
            evt = EventLog()

            # retrieves device attributes
            device_sec = event_dict['Device']
            evt.device_id = device_sec['ID']
            evt.device_fw = device_sec['Fw']
            evt.device_evt = device_sec['Evt']

            # retrieves report time
            evt.reported_time_utc = event_dict['UTC Time'][0]

            # retrieves alarm data
            # TODO: also attempt to get data from the correctly typed key?
            evt.coil_reversed = event_dict['Alarms']['CoilRevesed'] # possible typo in the dataset!

            # retrieves power attributes, normalizing types to float
            power_sec = event_dict['Power']
            evt.power_active_w = float(power_sec['Active'])
            # TODO: also attempt to get data from the correctly typed key?
            evt.power_apparent_va = float(power_sec['Appearent']) # possible typo in the dataset!
            evt.power_reactive_var = float(power_sec['Reactive'])

            # retrieves power line attributes, normalizing types to float
            line_sec = event_dict['Line']
            evt.line_current_a = float(line_sec['Current'])
            evt.line_phase_rad = float(line_sec['Phase'])
            evt.line_voltage_v = float(line_sec['Voltage'])
            # although hz isn't contained in the Line section, it's most likely related to it
            evt.line_frequency = float(event_dict['hz'][0])

            # retrieves harmonics
            evt.set_fft_harmonics_from_lists(event_dict['FFT Re'], event_dict['FFT Img'])

            # retrieves current peaks
            evt.set_peaks_from_list(event_dict['Peaks'])

            # retrieves dummy data, assuming it's actually useful :)
            evt.dummy_data = event_dict['Dummy'][0]

            # wifi sinal strength, normalizing to float
            evt.wifi_strength_dbm = float(event_dict['WiFi Strength'][0])

            # if we reached this point, all fields were correctly found
            return evt
        except:
            return None

    def set_fft_harmonics_from_lists(self, fft_real, fft_imaginary):
        """Builds the serialized representation of the fft_harmonics complex numbers."""
        if len(fft_real) != len(fft_imaginary):
            raise RuntimeError('Mismatched length for the two string parts.')
        complex_tuples = zip(fft_real, fft_imaginary)
        self.fft_harmonics = ''.join(['{},{};'.format(r, i) for r, i in complex_tuples])

    def set_peaks_from_list(self, peaks):
        """Builds the serialized represetnation of the current peaks list."""
        self.current_peaks_list = ''.join('{};'.format(p) for p in peaks)

    def get_fft_harmonics(self):
        """Returns a list of complex numbers parsed from the fft_harmonics field."""
        if not self.fft_harmonics:
            return []
        return parse_complex_list(self.fft_harmonics)

    def get_peaks(self):
        """Returns a list of float numbers representign the current_peaks_list field."""
        if not self.current_peaks_list:
            return []
        return parse_float_list(self.current_peaks_list)

class Cluster(BASE):
    """
    Stores the calculated calculated statistical data for each cluster
    Attributes:
        id                      Cluster label, used as the primary key for the table.
        count                   Number of elements associated with this cluster.
        avg_power_active_w      Average active power in watts for the associated elements.
        avg_power_reactive_var  Average reactive power in volt-ampere reactive for the associated
                                elements.
        avg_power_apparent_va   Average apparent power in volt-amper for the associated elements.
        avg_line_current_a      Average current in ampere for the associated elements.
        avg_line_voltage_v      Average voltage in volts for the associated elements.
    """
    __tablename__ = 'clusters'

    id = Column(Integer, primary_key=True, autoincrement=False)
    count = Column(Integer, default=0, nullable=False)
    avg_power_active_w = Column(Float, default=0.0, nullable=False)
    avg_power_reactive_var = Column(Float, default=0.0, nullable=False)
    avg_power_apparent_va = Column(Float, default=0.0, nullable=False)
    avg_line_current_a = Column(Float, default=0.0, nullable=False)
    avg_line_voltage_v = Column(Float, default=0.0, nullable=False)

    def __init__(self, label):
        assert isinstance(label, int)
        self.id = label
        self.count = 0
        self.avg_power_active_w = 0.0
        self.avg_power_reactive_var = 0.0
        self.avg_power_apparent_va = 0.0
        self.avg_line_current_a = 0.0
        self.avg_line_voltage_v = 0.0

    def to_dict(self):
        """
        Returns a dictionary representation of the cluster data.

        NOTE: There are a bunch of well-known hacks for outputing a dictionary from a SQLAlchemy
        model, but we decided to stick with the straight-forward implementation.
        """
        return {'label': self.id,
                'count': self.count,
                'avg_power_active_w': self.avg_power_active_w,
                'avg_power_reactive_var': self.avg_power_reactive_var,
                'avg_power_apparent_va': self.avg_power_apparent_va,
                'avg_line_current_a': self.avg_line_current_a,
                'avg_line_voltage_v': self.avg_line_voltage_v}

class EventCluster(BASE):
    """
    Stores data for the one-to-many relationship between Cluster and EventLog
    Although we could just add a nullable foreign key in the EventLog model, this approach attempts
    to isolate the cluster computation from log storage. In other words, once a log is stored it
    can be assumed to be read-only, as no updates will be necessary on the table.
    Attributes:
        cluster_id  Id (label) of the cluster.
        event_id    Id of the associated event.
    """

    __tablename__ = 'event_cluster'

    def __init__(self, cluster_id, event_id):
        assert isinstance(cluster_id, int)
        assert isinstance(event_id, int)
        self.cluster_id = cluster_id
        self.event_id = event_id

    cluster_id = Column(Integer, ForeignKey(Cluster.id), primary_key=True)
    event_id = Column(Integer, ForeignKey(EventLog.id), primary_key=True)
    event = relationship(EventLog)
    cluster = relationship(Cluster)


def parse_complex_list(string):
    """Returns a list of complex numbers parsed from the format used by the `events` table."""
    # filter all non-empty results of a split by ';'
    str_pairs = filter(lambda x: x, string.split(';'))
    # splits all elements by ',', resulting a list of tuples
    complex_str_list = map(lambda p: p.split(','), str_pairs)
    # converts all tuples to native 'complex' type
    complex_list = [complex(float(r), float(i)) for r, i in complex_str_list]
    return complex_list

def parse_float_list(string):
    str_floats = filter(lambda x: x, string.split(';'))
    return [float(x) for x in str_floats]

def get_db_sessionmaker(debug):
    """Returns a SQLAlchemy session for the application's SQLite db."""
    engine = create_engine('sqlite:///logservice.db', echo=debug)
    return sessionmaker(bind=engine)
