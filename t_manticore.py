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

t1()

# end of file
