#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import getpass
import json
import os
import time

import elasticsearch.helpers
import yaml
from elasticsearch import RequestsHttpConnection
from elasticsearch.client import Elasticsearch
from elasticsearch.client import IndicesClient
from elasticsearch.exceptions import NotFoundError
from envparse import Env

from .auth import Auth

env = Env(ES_USE_SSL=bool)

from datetime import datetime
from dateutil import tz
import sys
from .util import elasticsearch_client

class ReturnIndex(object):
    def parse_args(self):
        #if os.path.isfile('../config.yaml'):
        #    filename = '../config.yaml'
        #else:
        #    filename = ''

        filename = 'config.yaml'
        if filename:
            with open(filename) as config_file:
                data = yaml.load(config_file, Loader=yaml.FullLoader)
            host = data.get('es_host')
            port = data.get('es_port')
            username = data.get('es_username')
            password = data.get('es_password')
            url_prefix = data.get('es_url_prefix', '')
            use_ssl = data.get('use_ssl') is not False
            verify_certs = data.get('verify_certs') is not False
            aws_region = data.get('aws_region', None)
            send_get_body_as = data.get('send_get_body_as', 'GET')
            ca_certs = data.get('ca_certs')
            client_cert = data.get('client_cert')
            client_key = data.get('client_key')

        timeout = 60

        auth = Auth()
        http_auth = auth(host=host,
                     username=username,
                     password=password,
                     aws_region=aws_region,
                     profile_name=None)
        es = Elasticsearch(
            host=host,
            port=port,
            timeout=timeout,
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            connection_class=RequestsHttpConnection,
            http_auth=http_auth,
            url_prefix=url_prefix,
            send_get_body_as=send_get_body_as,
            client_cert=client_cert,
            ca_certs=ca_certs,
            client_key=client_key)

        return es

    def __init__(self):
        #self.es = self.parse_args()

    def send_to_es(self, body, conf, option):
        #es_client = self.es

        if os.path.isfile(conf):
            filename = conf
        elif os.path.isfile('../config.yaml'):
            filename = '../config.yaml'
        else:
            filename = ''

        es_client = elasticsearch_client(filename)

        doc = {
                    'message': body,
                    '@timestamp': datetime.now(tz=tz.tzlocal()),
                }

        # Get one document for schema
        try:
            if option == 'elasticsearch':
                #index = self.ea_index + '_test'
                index = 'elastalert_status_test'
                res = es_client.index(index, id=None, body=doc)
                print(res['result'])
        except Exception as e:
            print("Error running your filter:", file=sys.stderr)
            print(repr(e)[:2048], file=sys.stderr)