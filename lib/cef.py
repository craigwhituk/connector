#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Cef class"""
from lib.options import Options
import lib.loadyaml as loadyaml
import datetime


class Cef(object):
    """Cef class"""
    def __init__(self, options=None):
        self.options = options or Options()
        self.configs = loadyaml.load_cef()

    def cef_constants(self, event):
        """build cef constants"""
        severity = 9 if event["critical"] else 3
        try:
            event_type_id = self.configs["eventIdMap"][event["type"]]
        except KeyError:
            event_type_id = 999
        return "CEF:%s|%s|%s|%s|%s|%s|%s|" % (self.configs["cefVersion"],
                                              self.configs["cefVendor"],
                                              self.configs["cefProduct"],
                                              self.configs["cefProductVersion"],
                                              event_type_id,
                                              event["name"],
                                              severity)

    def build_cef_outliers(self, mapping, event):
        """build cef outliers"""
        mapping['deviceDirection'] = 1 if 'actor_username' in event else 0

    def format_cef_date(self, date):
        date_time = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        return date_time.strftime('%b %d %Y %H:%M:%S UTC')

    def build_cef_mapping(self, event):
        """build cef mapping"""
        mapping = {}
        self.build_cef_outliers(mapping, event)
        for key, value in self.configs['cefFieldMapping'].items():
            if key in event:
                if key == "created_at":
                    cef_date = self.format_cef_date(event[key])
                    mapping[value] = cef_date
                else:
                    mapping[value] = event[key]
                    if value in ['cs1', 'cs2', 'cs3', 'cs4']:
                        label = "%sLabel" % value
                        mapping[label] = self.configs['cefCsLabels'][label]
                del event[key]
        if event:
            mapping["cs5Label"] = self.configs['cefCsLabels']['cs5Label']
            mapping["cs5"] = event
        return mapping

    def format_cef(self, batched):
        """format cef"""
        aggregated_cef = []
        for event in batched:
            cef_str = ""
            constants_map = self.cef_constants(event)
            schema = self.build_cef_mapping(event)
            for key, value in schema.items():
                cef_str += "%s=%s " % (key, value)
            aggregated_cef.append("%s%s" % (constants_map, cef_str))
        return aggregated_cef
