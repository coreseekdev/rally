# -*- coding:utf-8 -*-
"""
测试 manticore 为 es 兼容的代码片段
"""
import MySQLdb


def get_conn(host='127.0.01', port=9306):
    return MySQLdb.connect(host=host, port=port)


def t1():
    conn = get_conn()
    cursor = conn.cursor()
    try:
        rs = cursor.execute("SHOW TABLES")
        for row in cursor.fetchall():
            print(row)
    finally:
        cursor.close()
    conn.close()

def toManticoreFieldName(esFieldName):
    return esFieldName.replace('@', '_')

def toManticoreIndexName(esIndex):
    return esIndex.replace('-', '_')

import ujson

class DataFeeder:
    def __init__(self, flush_cb=None):
        self._index_name = None
        self._items = []
        self.flush_cb = flush_cb
    
    def feed(self, data):
        if data:
            obj = ujson.loads(data)
            if 'index' in obj:
                index_name = obj['index']['_index']
                if index_name != self._index_name:
                    self.flush()
                    self._index_name = index_name
            else:
                self._items.append(obj)
        else:
            self.flush()
    
    def flush(self):
        ret = True

        if self._items:    
            if self.flush_cb:
                # do real insert
                ret = self.flush_cb(self._index_name, self._items)
            
            if ret:
                self._items = []
        return ret

class DataFlusher:
    def __init__(self, conn):
        self.conn = conn
    
    def __call__(self, index_name, items):
        if len(items):
            item = items[0]
            keys = item.keys()
            fields = map(lambda x: toManticoreFieldName(x), keys)
            sql = "INSERT INTO {}({}) VALUES ({})".format(toManticoreIndexName(index_name), ", ".join(fields), ", ".join(["%s"]*len(keys)))
            values = [tuple(x.values()) for x in items]
            cursor = self.conn.cursor()
            try:
                cursor.executemany(sql, values)
                #Commit your changes
                self.conn.commit()
            finally:
                cursor.close()

            #print(sql, len(items))
        return True

def t2():
    ctx = """{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"50.117.0.0", "request": "GET /english/images/lateb_new.gif HTTP/1.0", "status": 200, "size": 1431}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"122.117.0.0", "request": "GET /images/logo_cfo.gif HTTP/1.0", "status": 200, "size": 1504}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"122.117.0.0", "request": "GET /images/space.gif HTTP/1.0", "status": 200, "size": 42}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"122.117.0.0", "request": "GET /english/images/hm_official.gif HTTP/1.0", "status": 200, "size": 1807}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"122.117.0.0", "request": "GET /english/images/nav_venue_off.gif HTTP/1.0", "status": 200, "size": 870}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"122.117.0.0", "request": "GET /english/ProScroll.class HTTP/1.0", "status": 200, "size": 6507}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"112.117.0.0", "request": "GET /images/hm_arw.gif HTTP/1.0", "status": 200, "size": 1050}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"172.7.0.0", "request": "GET /images/s102320.gif HTTP/1.0", "status": 304, "size": 0}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"50.117.0.0", "request": "GET /english/images/archives.gif HTTP/1.0", "status": 200, "size": 869}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"50.117.0.0", "request": "GET /images/ligne01.gif HTTP/1.0", "status": 200, "size": 169}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"85.117.0.0", "request": "GET /images/ligneb01.gif HTTP/1.0", "status": 200, "size": 169}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"111.117.0.0", "request": "GET /english/nav_inet.html HTTP/1.1", "status": 200, "size": 2672}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"50.117.0.0", "request": "GET /images/dburton.jpg HTTP/1.0", "status": 200, "size": 12009}
{"index": {"_index": "logs-181998"}}
{"@timestamp": 894116672, "clientip":"111.117.0.0", "request": "GET /english/splash_inet.html HTTP/1.1", "status": 200, "size": 3723}
"""
    import MySQLdb
    host = '127.0.0.1'
    conn = MySQLdb.connect(host=host, port=9306)

    feeder = DataFeeder(DataFlusher(conn))
    for l in ctx.split('\n'):
        # print(l)
        feeder.feed(l)
    feeder.flush()

# t1()

t2()


# end of file
