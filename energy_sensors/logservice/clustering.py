#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Provides utilities for triggering clustering computations for database rows."""

import threading
import logging
from energy_sensors.logservice.db import Cluster, get_db_sessionmaker, EventLog, EventCluster
from sklearn.cluster import MeanShift, estimate_bandwidth
import numpy as np

class ClusteringBatchWorker(object):
    """"
    Triggers clustering computations when a target event count is reached.
    This class provides only one "public" event `report_event_received`, which should can be called
    to increment the current count. When the batch size is reached, a new worker thread is spawned
    and will run the entire workflow for refreshing cluster data on the database. This prevents
    high-latency for users, as the main thread won't need to stop serving until the computation is
    finished.

    KNOWN ISSUE: sklearn doesn't support multiprocessing-backed parallelism if ran outside the main
    thread. As a result of this, only the worker thread will be used to run the computation.
    A proper fix might be splitting the log and clustering services into two separate entities.
    """

    def __init__(self, batch_size=1000):
        self.running = False
        self.batch_size = batch_size
        self.count = 0
        self.worker_thread = None

    def report_event_received(self):
        """Reports new events, triggering the computation if the target count is reached."""
        self.count += 1
        if self.count >= self.batch_size:
            self.count = 0
            if self.worker_thread and self.worker_thread.is_alive():
                logging.warning('Previous computation isn\'t finished, but a new batch was formed')
                self.worker_thread.join()
            self.worker_thread = threading.Thread(target=self._compute_clusters)
            self.worker_thread.start()

    def _compute_clusters(self):
        """Triggers a new computation for the dataset."""
        session = get_db_sessionmaker(debug=False)()
        all_events = session.query(EventLog).all()
        dataset = self._collect_dataset(all_events)

        # runs the mean shift algorithm on the collected dataset
        mean_shift = self._run_mean_shift(dataset)
        if mean_shift is None:
            logging.error('Cluster computation failed!')
            return

        # calculates cluster statists related to event fit
        cluster_stats = self._calculate_cluster_stats(all_events, mean_shift)
        if not cluster_stats:
            logging.error('Cluster statistics computation failed!')
            return

        # if all calculations were sucessful, refresh database
        self._update_cluster_storage(session, all_events, mean_shift, cluster_stats)

    def _run_mean_shift(self, data):
        """Runs the mean shift algorithm on desired dataset."""
        bandwidth = estimate_bandwidth(data, quantile=0.2, n_samples=200)
        ms = MeanShift(bandwidth=bandwidth, cluster_all=False, bin_seeding=True)
        ms.fit_predict(data)
        return ms

    def _collect_dataset(self, event_results):
        """Returns a 2D array of clustering features relevant to a given event list"""
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

    def _calculate_cluster_stats(self, events, mean_shift):
        """Returns a dictionary associating each cluster label with it's elements' statistics."""
        # NOTE: is there a more elegant way of doing this?
        stats = {}
        event_labels = zip(events, mean_shift.labels_)
        for event, label in event_labels:
            # loop accumulate all values for the new clusters
            if label not in stats:
                stats[label] = Cluster(int(label))
            cluster = stats[label]
            cluster.count += 1
            cluster.avg_power_active_w += event.power_active_w
            cluster.avg_power_reactive_var += event.power_reactive_var
            cluster.avg_power_apparent_va += event.power_apparent_va
            cluster.avg_line_current_a += event.line_current_a
            cluster.avg_line_voltage_v += event.line_voltage_v

        for cluster in stats.values():
            # calculates the mean for each attribute
            count = float(cluster.count)
            cluster.avg_power_active_w /= count
            cluster.avg_power_reactive_var /= count
            cluster.avg_power_apparent_va /= count
            cluster.avg_line_current_a /= count
            cluster.avg_line_voltage_v /= count

        return stats

    def _update_cluster_storage(self, session, events, mean_shift, cluster_stats):
        """Purges previous cluster information, re-inserting the new values."""
        # deletes all previous cluster data
        session.query(Cluster).delete()
        session.query(EventCluster).delete()
        # creates and saves a list of object mappers representing clusters
        clusters = [EventCluster(int(cid), int(e.id)) for cid, e in zip(mean_shift.labels_, events)]
        session.bulk_save_objects(clusters)
        # stores cluster statistcs
        session.bulk_save_objects(cluster_stats.values())
        # commits transaction
        session.commit()
