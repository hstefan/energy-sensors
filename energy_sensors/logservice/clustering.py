#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Provides utilities for triggering clustering computations for database rows."""

import threading
import logging
from energy_sensors.logservice.db import get_db_sessionmaker, EventLog, EventCluster, parse_float_list
from sklearn.cluster import MeanShift, estimate_bandwidth
import numpy as np

class ClusteringBatchWorker(object):

    def __init__(self, batch_size=1000):
        self.running = False
        self.batch_size = batch_size
        self.count = 0
        self.worker_thread = threading.Thread(target=self._compute_clusters)

    def report_event_received(self):
        """Reports new events, triggering the computation if the target count is reached."""
        self.count += 1
        if self.count >= self.batch_size:
            self.count = 0
            if self.worker_thread.is_alive():
                logging.warning('Previous computation isn\'t finished, but a new batch was formed')
                self.worker_thread.join()
            self.worker_thread.start()

    def _compute_clusters(self):
        """Triggers a new computation for the dataset."""
        session = get_db_sessionmaker(debug=False)()
        all_events = session.query(EventLog).all()
        dataset = self._collect_dataset(all_events)
        mean_shift = self._run_mean_shift(dataset)
        if mean_shift is not None:
            self._update_cluster_storage(session, all_events, mean_shift)
        else:
            logging.error('Cluster computation failed')

    def _run_mean_shift(self, data):
        """Runs the mean shift algorithm on desired dataset."""
        bandwidth = estimate_bandwidth(data, quantile=0.2, n_samples=200)
        ms = MeanShift(bandwidth=bandwidth, cluster_all=False, bin_seeding=True)
        ms.fit_predict(data)
        return ms

    def _collect_dataset(self, event_results):
        dataset = []
        feature_count = 0
        sample_count = 0
        for event in event_results:
            assert isinstance(event, EventLog)
            pw_active = event.power_active_w
            pw_reactive = event.power_reactive_var
            pw_apparent = event.power_apparent_va
            ln_voltage = event.line_voltage_v
            ln_current = event.line_current_a
            # NOTE: transients are also called peaks
            transients = event.get_peaks()[:3] # only the first 3 values are relevant
            features = [pw_active, pw_reactive, pw_apparent, ln_current, ln_voltage]
            features.extend(transients)
            feature_count = len(features)
            sample_count += 1
            dataset.extend(features)
        feature_array = np.array(dataset)
        feature_array.shape = [sample_count, feature_count]
        return feature_array

    def _update_cluster_storage(self, session, events, mean_shift):
        """Purges previous cluster information, re-inserting the new values."""
        # deletes all previous cluster data
        session.query(EventCluster).delete()
        # creates and saves a list of object mappers representing clusters
        clusters = [EventCluster(int(cid), e.id) for cid, e in zip(mean_shift.labels_, events)]
        session.bulk_save_objects(clusters)
        session.commit()
