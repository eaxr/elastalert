#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import copy
import datetime
import json
import logging
import random
import re
import string
import sys

import mock

from .config import load_conf
from elastalert.elastalert import ElastAlerter
from elastalert.util import EAException
from elastalert.util import elasticsearch_client
from elastalert.util import lookup_es_key
from elastalert.util import ts_now
from elastalert.util import ts_to_dt

from datetime import datetime
from dateutil import tz

logging.getLogger().setLevel(logging.INFO)
logging.getLogger('elasticsearch').setLevel(logging.WARNING)

class ReturnIndex(object):
    def parse_args(self, args):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--config',
            action='store',
            dest='config',
            default="config.yaml",
            help='Global config file (default: config.yaml)')
        parser.add_argument('--debug', action='store_true', dest='debug', help='Suppresses alerts and prints information instead. '
                                                                               'Not compatible with `--verbose`')
        parser.add_argument('--rule', dest='rule', help='Run only a specific rule (by filename, must still be in rules folder)')
        parser.add_argument('--silence', dest='silence', help='Silence rule for a time period. Must be used with --rule. Usage: '
                                                              '--silence <units>=<number>, eg. --silence hours=2')
        parser.add_argument('--start', dest='start', help='YYYY-MM-DDTHH:MM:SS Start querying from this timestamp. '
                                                          'Use "NOW" to start from current time. (Default: present)')
        parser.add_argument('--end', dest='end', help='YYYY-MM-DDTHH:MM:SS Query to this timestamp. (Default: present)')
        parser.add_argument('--verbose', action='store_true', dest='verbose', help='Increase verbosity without suppressing alerts. '
                                                                                   'Not compatible with `--debug`')
        parser.add_argument('--patience', action='store', dest='timeout',
                            type=parse_duration,
                            default=datetime.timedelta(),
                            help='Maximum time to wait for ElasticSearch to become responsive.  Usage: '
                            '--patience <units>=<number>. e.g. --patience minutes=5')
        parser.add_argument(
            '--pin_rules',
            action='store_true',
            dest='pin_rules',
            help='Stop ElastAlert from monitoring config file changes')
        parser.add_argument('--es_debug', action='store_true', dest='es_debug', help='Enable verbose logging from Elasticsearch queries')
        parser.add_argument(
            '--es_debug_trace',
            action='store',
            dest='es_debug_trace',
            help='Enable logging from Elasticsearch queries as curl command. Queries will be logged to file. Note that '
                 'this will incorrectly display localhost:9200 as the host/port')
        self.args = parser.parse_args(args)

    def __init__(self, args):
        self.parse_args(args)
        self.data = []
        self.formatted_output = {}
        self.conf = load_conf(self.args)

    def send_to_es(self, option, conf, args):
        """ Loads a rule config file, performs a query over the last day (args.days), lists available keys
        and prints the number of results. """
        if args.schema_only:
            return []

        # Set up Elasticsearch client and query
        es_client = elasticsearch_client(conf)

        # Get one document for schema
        try:
            if option == 'elasticsearch':
                doc = {
                    'text': 'test from ElastAlert',
                    '@timestamp': datetime.now(tz=tz.tzlocal()),
                }

                #index = self.ea_index + '_test'
                index = 'elastalert_status_test'
                res = es_client.index(index, id=None, body=doc)
                print(res['result'])
        except Exception as e:
            print("Error running your filter:", file=sys.stderr)
            print(repr(e)[:2048], file=sys.stderr)