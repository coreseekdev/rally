# -*- coding:utf-8 -*-
"""
    将指定位置的编译好的 manticore 二进制打包为 测试使用的 release 模式

参数

    1. 编译完毕的目录
    2. 指派的版本
"""
import os
import sys
import tarfile

fpath = os.path.abspath(sys.argv[1])
tagged_version = sys.argv[2]


fname = os.path.join(os.path.expanduser('~'), '.rally/benchmarks/distributions/', 'release-{}-manticore-linux-x86_64.tar.gz'.format(tagged_version))

tar = tarfile.open(fname,"w:gz")

for f in ['indexer', 'indextool', 'searchd', 'spelldump', 'wordbreaker']:
    full_f = os.path.join(fpath, 'src',f)
    tar.add(full_f, os.path.join('manticore-{}'.format(tagged_version),'bin', f))

tar.close()
