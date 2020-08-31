# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import contextvars
import logging
import time

import certifi
import urllib3

from esrally import exceptions, doc_link
from esrally.utils import console, convert


class EsClientFactory:
    """
    Abstracts how the Elasticsearch client is created. Intended for testing.
    """
    def __init__(self, hosts, client_options):
        self.hosts = hosts
        self.client_options = dict(client_options)
        self.ssl_context = None
        self.logger = logging.getLogger(__name__)

        masked_client_options = dict(client_options)
        if "basic_auth_password" in masked_client_options:
            masked_client_options["basic_auth_password"] = "*****"
        if "http_auth" in masked_client_options:
            masked_client_options["http_auth"] = (masked_client_options["http_auth"][0], "*****")
        self.logger.info("Creating ES client connected to %s with options [%s]", hosts, masked_client_options)

        # we're using an SSL context now and it is not allowed to have use_ssl present in client options anymore
        if self.client_options.pop("use_ssl", False):
            import ssl
            self.logger.info("SSL support: on")
            self.client_options["scheme"] = "https"

            # ssl.Purpose.CLIENT_AUTH allows presenting client certs and can only be enabled during instantiation
            # but can be disabled via the verify_mode property later on.
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH,
                                                          cafile=self.client_options.pop("ca_certs", certifi.where()))

            if not self.client_options.pop("verify_certs", True):
                self.logger.info("SSL certificate verification: off")
                # order matters to avoid ValueError: check_hostname needs a SSL context with either CERT_OPTIONAL or CERT_REQUIRED
                self.ssl_context.verify_mode = ssl.CERT_NONE
                self.ssl_context.check_hostname = False

                self.logger.warning("User has enabled SSL but disabled certificate verification. This is dangerous but may be ok for a "
                                    "benchmark. Disabling urllib warnings now to avoid a logging storm. "
                                    "See https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings for details.")
                # disable:  "InsecureRequestWarning: Unverified HTTPS request is being made. Adding certificate verification is strongly \
                # advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings"
                urllib3.disable_warnings()
            else:
                self.ssl_context.verify_mode=ssl.CERT_REQUIRED
                self.ssl_context.check_hostname = True
                self.logger.info("SSL certificate verification: on")

            # When using SSL_context, all SSL related kwargs in client options get ignored
            client_cert = self.client_options.pop("client_cert", False)
            client_key = self.client_options.pop("client_key", False)

            if not client_cert and not client_key:
                self.logger.info("SSL client authentication: off")
            elif bool(client_cert) != bool(client_key):
                self.logger.error(
                    "Supplied client-options contain only one of client_cert/client_key. "
                )
                defined_client_ssl_option = "client_key" if client_key else "client_cert"
                missing_client_ssl_option = "client_cert" if client_key else "client_key"
                console.println(
                    "'{}' is missing from client-options but '{}' has been specified.\n"
                    "If your Elasticsearch setup requires client certificate verification both need to be supplied.\n"
                    "Read the documentation at {}\n".format(
                        missing_client_ssl_option,
                        defined_client_ssl_option,
                        console.format.link(doc_link("command_line_reference.html#client-options")))
                )
                raise exceptions.SystemSetupError(
                    "Cannot specify '{}' without also specifying '{}' in client-options.".format(
                        defined_client_ssl_option,
                        missing_client_ssl_option))
            elif client_cert and client_key:
                self.logger.info("SSL client authentication: on")
                self.ssl_context.load_cert_chain(certfile=client_cert,
                                                 keyfile=client_key)
        else:
            self.logger.info("SSL support: off")
            self.client_options["scheme"] = "http"

        if self._is_set(self.client_options, "basic_auth_user") and self._is_set(self.client_options, "basic_auth_password"):
            self.logger.info("HTTP basic authentication: on")
            self.client_options["http_auth"] = (self.client_options.pop("basic_auth_user"), self.client_options.pop("basic_auth_password"))
        else:
            self.logger.info("HTTP basic authentication: off")

        if self._is_set(self.client_options, "compressed"):
            console.warn("You set the deprecated client option 'compressed‘. Please use 'http_compress' instead.", logger=self.logger)
            self.client_options["http_compress"] = self.client_options.pop("compressed")

        if self._is_set(self.client_options, "http_compress"):
            self.logger.info("HTTP compression: on")
        else:
            self.logger.info("HTTP compression: off")

        if self._is_set(self.client_options, "enable_cleanup_closed"):
            self.client_options["enable_cleanup_closed"] = convert.to_bool(self.client_options.pop("enable_cleanup_closed"))

    def _is_set(self, client_opts, k):
        try:
            return client_opts[k]
        except KeyError:
            return False

    def create(self):
        import elasticsearch
        return elasticsearch.Elasticsearch(hosts=self.hosts, ssl_context=self.ssl_context, **self.client_options)

    def create_async(self):
        import elasticsearch
        import esrally.async_connection
        import io
        import aiohttp

        from elasticsearch.serializer import JSONSerializer

        class LazyJSONSerializer(JSONSerializer):
            def loads(self, s):
                meta = RallyAsyncElasticsearch.request_context.get()
                if "raw_response" in meta:
                    return io.BytesIO(s)
                else:
                    return super().loads(s)

        async def on_request_start(session, trace_config_ctx, params):
            meta = RallyAsyncElasticsearch.request_context.get()
            # this can happen if multiple requests are sent on the wire for one logical request (e.g. scrolls)
            if "request_start" not in meta:
                meta["request_start"] = time.perf_counter()

        async def on_request_end(session, trace_config_ctx, params):
            meta = RallyAsyncElasticsearch.request_context.get()
            meta["request_end"] = time.perf_counter()

        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_start.append(on_request_start)
        trace_config.on_request_end.append(on_request_end)
        # ensure that we also stop the timer when a request "ends" with an exception (e.g. a timeout)
        trace_config.on_request_exception.append(on_request_end)

        # override the builtin JSON serializer
        self.client_options["serializer"] = LazyJSONSerializer()
        self.client_options["trace_config"] = trace_config

        class RallyAsyncElasticsearch(elasticsearch.AsyncElasticsearch):
            request_context = contextvars.ContextVar("rally_request_context")

            def init_request_context(self):
                ctx = {}
                RallyAsyncElasticsearch.request_context.set(ctx)
                return ctx

            def return_raw_response(self):
                ctx = RallyAsyncElasticsearch.request_context.get()
                ctx["raw_response"] = True

        return RallyAsyncElasticsearch(hosts=self.hosts,
                                       connection_class=esrally.async_connection.AIOHttpConnection,
                                       ssl_context=self.ssl_context,
                                       **self.client_options)


def wait_for_rest_layer(es, max_attempts=40):
    """
    Waits for ``max_attempts`` until Elasticsearch's REST API is available.

    :param es: Elasticsearch client to use for connecting.
    :param max_attempts: The maximum number of attempts to check whether the REST API is available.
    :return: True iff Elasticsearch's REST API is available.
    """
    # assume that at least the hosts that we expect to contact should be available. Note that this is not 100%
    # bullet-proof as a cluster could have e.g. dedicated masters which are not contained in our list of target hosts
    # but this is still better than just checking for any random node's REST API being reachable.
    expected_node_count = len(es.transport.hosts)
    logger = logging.getLogger(__name__)
    for attempt in range(max_attempts):
        logger.debug("REST API is available after %s attempts", attempt)
        import elasticsearch
        try:
            # see also WaitForHttpResource in Elasticsearch tests. Contrary to the ES tests we consider the API also
            # available when the cluster status is RED (as long as all required nodes are present)
            es.cluster.health(wait_for_nodes=">={}".format(expected_node_count))
            logger.info("REST API is available for >= [%s] nodes after [%s] attempts.", expected_node_count, attempt)
            return True
        except elasticsearch.ConnectionError as e:
            if "SSL: UNKNOWN_PROTOCOL" in str(e):
                raise exceptions.SystemSetupError("Could not connect to cluster via https. Is this an https endpoint?", e)
            else:
                logger.debug("Got connection error on attempt [%s]. Sleeping...", attempt)
                time.sleep(3)
        except elasticsearch.TransportError as e:
            # cluster block, x-pack not initialized yet, our wait condition is not reached
            if e.status_code in (503, 401, 408):
                logger.debug("Got status code [%s] on attempt [%s]. Sleeping...", e.status_code, attempt)
                time.sleep(3)
            else:
                logger.warning("Got unexpected status code [%s] on attempt [%s].", e.status_code, attempt)
                raise e
    return False

"""
    为兼容 ES API 接口， 实现的 LazyLoad 对象
"""
import functools

def async_context():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            # print (args[0].url)
            # Some fancy foo stuff
            meta = args[0]._mc_conn.ctx
            if "request_start" not in meta:
                meta["request_start"] = time.perf_counter()
            v = await func(*args, **kwargs)
            meta["request_end"] = time.perf_counter()
            return v

        return wrapped
    return wrapper

def async_context2():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            # print (args[0].url)
            # Some fancy foo stuff
            meta = args[0].ctx
            if "request_start" not in meta:
                meta["request_start"] = time.perf_counter()
            v = await func(*args, **kwargs)
            meta["request_end"] = time.perf_counter()
            return v

        return wrapped
    return wrapper

def toManticoreIndexName(esIndex):
    return esIndex.replace('-', '_')

def toManticoreFieldName(esFieldName):
    return esFieldName.replace('@', '_')

class LazyManticoreIndices(object):
    def __init__(self, conn):
        self._mc_conn = conn
        self.indices = []

    async def _fetch_index(self):
        """
        查询 manticore 中包括的 索引
        """
        indices = []
        conn = self._mc_conn.conn
        cursor = conn.cursor()
        try:
            rs = cursor.execute("SHOW TABLES")
            for row in cursor.fetchall():
                # index name, type
                indices.append(row[0])
        finally:
            cursor.close()
        return indices

    @async_context()
    async def exists(self, index):
        # check have cache?
        if not self.indices:
            self.indices = await self._fetch_index()
        # print(self._mc_conn.ctx)
        return index in self.indices

    @async_context()
    async def delete(self, index, params=None):
        conn = self._mc_conn.conn
        cursor = conn.cursor()
        try:
            rs = cursor.execute("DROP TABLE {}".format(toManticoreIndexName(index)))
        finally:
            cursor.close()
        return True
  
    @async_context()
    async def create(self, index, body, params):
        # {'settings': 
        #   {'index.number_of_shards': 5, 
        #    'index.number_of_replicas': 0, 
        #    'index.requests.cache.enable': False, 
        #    'index.sort.field': '@timestamp', 'index.sort.order': 'desc'}
        # CREATE TABLE distributed_index type='distributed' local='local_index'
        """
        'mappings': {
            'dynamic': 'strict', 
            '_source': {'enabled': True}, 
            'properties': {
                '@timestamp': {'format': 'strict_date_optional_time||epoch_second', 'type': 'date'}, 
                'clientip': {'type': 'ip'}, 
                'message': {'type': 'keyword', 'index': False, 'doc_values': False}, 
                'request': {'type': 'text', 'fields': {'raw': {'ignore_above': 256, 'type': 'keyword'}}}, 
                'status': {'type': 'integer'}, 'size': {'type': 'integer'}, 
                'geoip': {
                    'properties': {
                        'country_name': {'type': 'keyword'}, 
                        'city_name': {'type': 'keyword'}, 
                        'location': {'type': 'geo_point'}
                    }
                }
            }
        }} {}

        strict_date_optional_time||epoch_second
            允许字符串解析， 标准时间格式 或 milliseconds-since-the-epoch.
        ip
            支持 ipv4 或 ipv6 的字符串形式进入索引,
            ip 可以使用 CIDR 进行查询，或进行精确查询
            ip 可以视为 需要进行特殊处理的全文检索字段
        keyword
            处理为 string
        embed-type
            展开子 字段
        允许在 字段中，在索引时衍生字段，eg. raw
        integer
            int32
        geo_point   , 添加额外的字段 -lat 和 -lon
            "location": { 
                "lat": 41.12,
                "lon": -71.34
            }   
        """
        def toManticoreType(esType):
            es2manticore_mappting = {
                'date': 'timestamp',
                'ip':   'text',
                'keyword': 'string',
                'text': 'text',
                'integer': 'int'
            }
            if esType.lower() in es2manticore_mappting:
                return es2manticore_mappting[esType.lower()]
            return None
        
        def addAttribute(attr):
            if attr.get('indexed', False):
                return " attribute indexed"
            return ""

        index_name = index
        number_of_shards = body['settings']['index.number_of_shards']
        # field_name, type, options{}
        # eg. attribute indexed 
        fields_define = []
        for field, props in body['mappings']['properties'].items():
            if 'properties' in props:
                # hardcoded hack, skip geoip
                continue

            mcType = toManticoreType(props['type'])
            if mcType:
                attr = dict()
                # hardcoded hack for http_logs
                if 'fields' in props:
                    fields_define.append(
                        (field, 'string', {'indexed':True})
                    )
                else:
                    fields_define.append(
                        (field, mcType, attr)
                    )
        # create table products(title text stored indexed, content text stored indexed, name text indexed, price float)
        # CREATE TABLE products (title text indexed, description text stored, author text, price float)
        fields = map(lambda x: "{} {}".format(toManticoreFieldName(x[0]), x[1] + addAttribute(x[2])) , fields_define)
        sql = "CREATE TABLE {}({})".format(toManticoreIndexName(index_name), ', '.join(fields))
        # print(sql)
        #for field in fields_define:
        #    print(field)
        conn = self._mc_conn.conn
        cursor = conn.cursor()
        try:
            rs = cursor.execute(sql)
        finally:
            cursor.close()
        return True


class ManticoreTransport:
    def __init__(self, mc):
        self._mc_conn = mc

    @async_context()
    async def close(self):
        self._mc_conn.conn.close()

class ManticoreCluster:
    def __init__(self, mc):
        self._mc_conn = mc

    @async_context()
    async def health(self, index, params):
        # hard coded
        return {
            "status": 3,    # 3 for green .
            "relocating_shards": 0
        }

class ManticoreClientFactory:
    """
    Abstracts how the Manticore client is created. Intended for testing.
    """
    def __init__(self, hosts, client_options):
        self.hosts = hosts
        self.client_options = dict(client_options)
        self.ssl_context = None
        self.logger = logging.getLogger(__name__)

        masked_client_options = dict(client_options)
        if "basic_auth_password" in masked_client_options:
            masked_client_options["basic_auth_password"] = "*****"
        if "http_auth" in masked_client_options:
            masked_client_options["http_auth"] = (masked_client_options["http_auth"][0], "*****")
        self.logger.info("Creating ES client connected to %s with options [%s]", hosts, masked_client_options)

    def _is_set(self, client_opts, k):
        try:
            return client_opts[k]
        except KeyError:
            return False

    def create(self):
        import MySQLdb
        host = self.hosts[0]['host']
        return MySQLdb.connect(host=host, port=9306)

    def create_async(self):
        import asyncio
        import aiomysql
        import MySQLdb

        
        # 在 ES 的版本中，对 request 进行了追踪。
        # 目前暂时无法处理 aiomysql 的 req & res.
        # 暂时不处理 asyncio
        #conn = await aiomysql.connect(host=self.hosts[0], loop= asyncio.get_running_loop())
        #return conn
        host = self.hosts[0]['host']

        class RallyManticoreConnection(object):

            def __init__(self, host, port):
                self.conn = MySQLdb.connect(host=host, port=port)
                self.ctx = {}
                
                # init properties
                self.indices = LazyManticoreIndices(self)
                self.transport = ManticoreTransport(self)
                self.cluster = ManticoreCluster(self)
            
            def init_request_context(self):
                self.ctx = {}
                # 暂时处理为同步
                # RallyAsyncElasticsearch.request_context.set(ctx)
                return self.ctx

            def return_raw_response(self):
                # ctx = RallyAsyncElasticsearch.request_context.get()
                self.ctx["raw_response"] = True
            
            @async_context2()
            async def bulk(self, body, params):
                print(body, params)
                raise NotImplemented


        return RallyManticoreConnection(host=host, port=9306)

        """
        import elasticsearch
        import esrally.async_connection
        import io
        import aiohttp

        from elasticsearch.serializer import JSONSerializer

        class LazyJSONSerializer(JSONSerializer):
            def loads(self, s):
                meta = RallyAsyncElasticsearch.request_context.get()
                if "raw_response" in meta:
                    return io.BytesIO(s)
                else:
                    return super().loads(s)

        async def on_request_start(session, trace_config_ctx, params):
            meta = RallyAsyncElasticsearch.request_context.get()
            # this can happen if multiple requests are sent on the wire for one logical request (e.g. scrolls)
            if "request_start" not in meta:
                meta["request_start"] = time.perf_counter()

        async def on_request_end(session, trace_config_ctx, params):
            meta = RallyAsyncElasticsearch.request_context.get()
            meta["request_end"] = time.perf_counter()

        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_start.append(on_request_start)
        trace_config.on_request_end.append(on_request_end)
        # ensure that we also stop the timer when a request "ends" with an exception (e.g. a timeout)
        trace_config.on_request_exception.append(on_request_end)

        # override the builtin JSON serializer
        self.client_options["serializer"] = LazyJSONSerializer()
        self.client_options["trace_config"] = trace_config

        class RallyAsyncElasticsearch(elasticsearch.AsyncElasticsearch):
            request_context = contextvars.ContextVar("rally_request_context")

            def init_request_context(self):
                ctx = {}
                RallyAsyncElasticsearch.request_context.set(ctx)
                return ctx

            def return_raw_response(self):
                ctx = RallyAsyncElasticsearch.request_context.get()
                ctx["raw_response"] = True

        return RallyAsyncElasticsearch(hosts=self.hosts,
                                       connection_class=esrally.async_connection.AIOHttpConnection,
                                       ssl_context=self.ssl_context,
                                       **self.client_options)
        """
