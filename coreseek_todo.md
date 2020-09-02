# TODO

- [X] 为 `--distribution-version` 提供选项 `manticore`， 处理为 manticore 的测试分支

1. mechanic/launcher 需要调整为启动 searchd
2. "operation-type: 
        create-index
        cluster-health
        force-merge
        index-stats
        bulk
        refresh

2. 对 search 的客户端进行封装，尽量模拟 es

    + indeces 对象
    ++ delete(index=index_name, params=request_params) 
    ++ exists(index=index_name)
    ++ create(index=index, body=body, params=request_params)
    ++ refresh(index=params.get("index", "_all"))  // index 结束 和 merge 结束后调用
    ++ forcemerge(index=params.get("index"), max_num_segments=max_num_segments, request_timeout=request_timeout)
    ++ forcemerge(index=params.get("index"), request_timeout=request_timeout)

    + cluster
    ++  health(index=index, params=request_params)
    
    + bulk
    ++ es.bulk(body=params["body"], params=bulk_params)
    ++ es.bulk(body=params["body"], index=index, doc_type=params.get("type"), params=bulk_params)


3. 基于路径的检查

    + IndicesStats / index-stats

4. 对查询行为的实现，名字是 search

    + class Query(Runner):


# Benchmark

数据量：

- 3.17G ， 24.3M Docs , HTTP Log, JSON format

## ElasticSearch 7.8.1

### default car
$ time ./rally --distribution-version=7.8.1 --track-path=./track-http-logs --challenge append-sorted-no-conflicts  --client-options="http_compress:true" --kill-running-processes

PID    USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM  TIME+ COMMAND
107954 nzinfo    20   0 8227728   1.7g 294952 S 620.2   5.6  28:58.18 java  

Total write 11.7GB

|                                                         Metric |              Task |       Value |   Unit |
|---------------------------------------------------------------:|------------------:|------------:|-------:|
|                     Cumulative indexing time of primary shards |                   |     33.1065 |    min |
|             Min cumulative indexing time across primary shards |                   |           0 |    min |
|          Median cumulative indexing time across primary shards |                   |           0 |    min |
|             Max cumulative indexing time across primary shards |                   |     3.28512 |    min |
|            Cumulative indexing throttle time of primary shards |                   |           0 |    min |
|    Min cumulative indexing throttle time across primary shards |                   |           0 |    min |
| Median cumulative indexing throttle time across primary shards |                   |           0 |    min |
|    Max cumulative indexing throttle time across primary shards |                   |           0 |    min |
|                        Cumulative merge time of primary shards |                   |     6.23505 |    min |
|                       Cumulative merge count of primary shards |                   |          53 |        |
|                Min cumulative merge time across primary shards |                   |           0 |    min |
|             Median cumulative merge time across primary shards |                   |           0 |    min |
|                Max cumulative merge time across primary shards |                   |    0.661217 |    min |
|               Cumulative merge throttle time of primary shards |                   |      0.0013 |    min |
|       Min cumulative merge throttle time across primary shards |                   |           0 |    min |
|    Median cumulative merge throttle time across primary shards |                   |           0 |    min |
|       Max cumulative merge throttle time across primary shards |                   |      0.0005 |    min |
|                      Cumulative refresh time of primary shards |                   |      6.2874 |    min |
|                     Cumulative refresh count of primary shards |                   |         405 |        |
|              Min cumulative refresh time across primary shards |                   |           0 |    min |
|           Median cumulative refresh time across primary shards |                   |           0 |    min |
|              Max cumulative refresh time across primary shards |                   |       0.644 |    min |
|                        Cumulative flush time of primary shards |                   |           0 |    min |
|                       Cumulative flush count of primary shards |                   |          25 |        |
|                Min cumulative flush time across primary shards |                   |           0 |    min |
|             Median cumulative flush time across primary shards |                   |           0 |    min |
|                Max cumulative flush time across primary shards |                   |           0 |    min |
|                                        Total Young Gen GC time |                   |       19.36 |      s |
|                                       Total Young Gen GC count |                   |        1469 |        |
|                                          Total Old Gen GC time |                   |       1.997 |      s |
|                                         Total Old Gen GC count |                   |          42 |        |
|                                                     Store size |                   |     1.94452 |     GB |
|                                                  Translog size |                   | 2.04891e-06 |     GB |
|                                         Heap used for segments |                   |    0.306293 |     MB |
|                                       Heap used for doc values |                   |   0.0506706 |     MB |
|                                            Heap used for terms |                   |    0.139816 |     MB |
|                                            Heap used for norms |                   |   0.0114136 |     MB |
|                                           Heap used for points |                   |           0 |     MB |
|                                    Heap used for stored fields |                   |    0.104393 |     MB |
|                                                  Segment count |                   |         187 |        |
|                                                 Min Throughput | tiny-index-append |     43979.1 | docs/s |
|                                              Median Throughput | tiny-index-append |     81549.6 | docs/s |
|                                                 Max Throughput | tiny-index-append |     84994.3 | docs/s |
|                                        50th percentile latency | tiny-index-append |     295.366 |     ms |
|                                        90th percentile latency | tiny-index-append |     472.827 |     ms |
|                                        99th percentile latency | tiny-index-append |     2058.97 |     ms |
|                                      99.9th percentile latency | tiny-index-append |     2934.07 |     ms |
|                                       100th percentile latency | tiny-index-append |      4963.2 |     ms |
|                                   50th percentile service time | tiny-index-append |     295.366 |     ms |
|                                   90th percentile service time | tiny-index-append |     472.827 |     ms |
|                                   99th percentile service time | tiny-index-append |     2058.97 |     ms |
|                                 99.9th percentile service time | tiny-index-append |     2934.07 |     ms |
|                                  100th percentile service time | tiny-index-append |      4963.2 |     ms |
|                                                     error rate | tiny-index-append |           0 |      % |


---------------------------------
[INFO] SUCCESS (took 370 seconds)
---------------------------------

real	6m13.176s
user	0m2.340s
sys	0m0.219s


## Manticore

$ ./rally --distribution-version=3.5.0-manticore --track-path=./track-http-logs --challenge append-sorted-no-conflicts --car=8gheap --client-options="http_compress:true" --kill-running-processes


PID    USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM  TIME+ COMMAND
106983 nzinfo    20   0 2329656   1.9g   1.3g S 368.4   6.2  11:53.52 searchd  
106983 nzinfo    20   0 2927404   2.4g   1.7g S  99.3   7.8  16:19.38 searchd

Total write 7.4GB
            
|                         Metric |              Task |   Value |   Unit |
|-------------------------------:|------------------:|--------:|-------:|
|                 Min Throughput | tiny-index-append | 88045.4 | docs/s |
|              Median Throughput | tiny-index-append | 92148.1 | docs/s |
|                 Max Throughput | tiny-index-append | 95545.7 | docs/s |
|        50th percentile latency | tiny-index-append | 329.957 |     ms |
|        90th percentile latency | tiny-index-append | 391.326 |     ms |
|        99th percentile latency | tiny-index-append |    1800 |     ms |
|      99.9th percentile latency | tiny-index-append | 2539.37 |     ms |
|       100th percentile latency | tiny-index-append | 3188.47 |     ms |
|   50th percentile service time | tiny-index-append | 329.957 |     ms |
|   90th percentile service time | tiny-index-append | 391.326 |     ms |
|   99th percentile service time | tiny-index-append |    1800 |     ms |
| 99.9th percentile service time | tiny-index-append | 2539.37 |     ms |
|  100th percentile service time | tiny-index-append | 3188.47 |     ms |
|                     error rate | tiny-index-append |       0 |      % |


---------------------------------
[INFO] SUCCESS (took 339 seconds)
---------------------------------

real	5m42.394s
user	0m2.590s
sys	0m0.232s


## Summary

在 micro benchmark 中， 

- Manticore 的方案，磁盘写入量 7.4G vs 11.7GB , 为 ES 的 63.2%
- 建立索引的时间 339s vs. 370s ， 耗时为 ES 的 91.6 %
- CPU 占用率（平均近似） 368 vs 600 ， 为 ES 的 61.3% ， 进一步优化调度后速度有望进一步提升
- Max Throughput 最大文档吞吐量 95545.7 vs 84994.3 , 为 ES 的 112%
- Min Throughput 88045.4 vs 43979.1 为 ES 的 200%
- 90%请求时延 2539.37ms vs 2934.07ms 为 ES 的 86.5%
- 事物性写入，不存在部分写入成功的情况



## ES on 33G

            
|                                                         Metric |                      Task |       Value |   Unit |
|---------------------------------------------------------------:|--------------------------:|------------:|-------:|
|                     Cumulative indexing time of primary shards |                           |     272.637 |    min |
|             Min cumulative indexing time across primary shards |                           |           0 |    min |
|          Median cumulative indexing time across primary shards |                           |     2.86537 |    min |
|             Max cumulative indexing time across primary shards |                           |     46.4525 |    min |
|            Cumulative indexing throttle time of primary shards |                           |           0 |    min |
|    Min cumulative indexing throttle time across primary shards |                           |           0 |    min |
| Median cumulative indexing throttle time across primary shards |                           |           0 |    min |
|    Max cumulative indexing throttle time across primary shards |                           |           0 |    min |
|                        Cumulative merge time of primary shards |                           |     147.056 |    min |
|                       Cumulative merge count of primary shards |                           |         420 |        |
|                Min cumulative merge time across primary shards |                           |           0 |    min |
|             Median cumulative merge time across primary shards |                           |      0.7051 |    min |
|                Max cumulative merge time across primary shards |                           |     31.8299 |    min |
|               Cumulative merge throttle time of primary shards |                           |     38.4837 |    min |
|       Min cumulative merge throttle time across primary shards |                           |           0 |    min |
|    Median cumulative merge throttle time across primary shards |                           |           0 |    min |
|       Max cumulative merge throttle time across primary shards |                           |     10.1029 |    min |
|                      Cumulative refresh time of primary shards |                           |     48.4984 |    min |
|                     Cumulative refresh count of primary shards |                           |        1705 |        |
|              Min cumulative refresh time across primary shards |                           |           0 |    min |
|           Median cumulative refresh time across primary shards |                           |      0.5977 |    min |
|              Max cumulative refresh time across primary shards |                           |     7.78722 |    min |
|                        Cumulative flush time of primary shards |                           |     3.65092 |    min |
|                       Cumulative flush count of primary shards |                           |         122 |        |
|                Min cumulative flush time across primary shards |                           |           0 |    min |
|             Median cumulative flush time across primary shards |                           |   0.0216333 |    min |
|                Max cumulative flush time across primary shards |                           |    0.802217 |    min |
|                                        Total Young Gen GC time |                           |     121.524 |      s |
|                                       Total Young Gen GC count |                           |       13867 |        |
|                                          Total Old Gen GC time |                           |      17.922 |      s |
|                                         Total Old Gen GC count |                           |         378 |        |
|                                                     Store size |                           |     15.8295 |     GB |
|                                                  Translog size |                           | 1.99769e-06 |     GB |
|                                         Heap used for segments |                           |    0.893215 |     MB |
|                                       Heap used for doc values |                           |    0.116703 |     MB |
|                                            Heap used for terms |                           |    0.360077 |     MB |
|                                            Heap used for norms |                           |    0.031311 |     MB |
|                                           Heap used for points |                           |           0 |     MB |
|                                    Heap used for stored fields |                           |    0.385124 |     MB |
|                                                  Segment count |                           |         513 |        |
|                                                 Min Throughput |              index-append |     15700.9 | docs/s |
|                                              Median Throughput |              index-append |     69682.1 | docs/s |
|                                                 Max Throughput |              index-append |     82966.9 | docs/s |
|                                        50th percentile latency |              index-append |     290.841 |     ms |
|                                        90th percentile latency |              index-append |     10936.4 |     ms |
|                                        99th percentile latency |              index-append |       10968 |     ms |
|                                      99.9th percentile latency |              index-append |     10978.9 |     ms |
|                                     99.99th percentile latency |              index-append |     10980.5 |     ms |
|                                       100th percentile latency |              index-append |     10984.3 |     ms |
|                                   50th percentile service time |              index-append |     290.841 |     ms |
|                                   90th percentile service time |              index-append |     10936.4 |     ms |
|                                   99th percentile service time |              index-append |       10968 |     ms |
|                                 99.9th percentile service time |              index-append |     10978.9 |     ms |
|                                99.99th percentile service time |              index-append |     10980.5 |     ms |
|                                  100th percentile service time |              index-append |     10984.3 |     ms |
|                                                     error rate |              index-append |       14.12 |      % |
|                                       100th percentile latency |       refresh-after-index |     10872.1 |     ms |
|                                  100th percentile service time |       refresh-after-index |     10872.1 |     ms |
|                                                     error rate |       refresh-after-index |         100 |      % |
|                                       100th percentile latency | refresh-after-force-merge |     10826.2 |     ms |
|                                  100th percentile service time | refresh-after-force-merge |     10826.2 |     ms |
|                                                     error rate | refresh-after-force-merge |         100 |      % |

[WARNING] Error rate is 14.12 for operation 'index-append'. Please check the logs.
[WARNING] Error rate is 100.0 for operation 'refresh-after-index'. Please check the logs.
[WARNING] No throughput metrics available for [refresh-after-index]. Likely cause: Error rate is 100.0%. Please check the logs.
[WARNING] Error rate is 100.0 for operation 'refresh-after-force-merge'. Please check the logs.
[WARNING] No throughput metrics available for [refresh-after-force-merge]. Likely cause: Error rate is 100.0%. Please check the logs.

-----------------------------------
[INFO] SUCCESS (took 13619 seconds)
-----------------------------------



## MC on 33G

            
|                          Metric |         Task |   Value |   Unit |
|--------------------------------:|-------------:|--------:|-------:|
|                  Min Throughput | index-append | 71908.7 | docs/s |
|               Median Throughput | index-append | 74028.2 | docs/s |
|                  Max Throughput | index-append | 98620.8 | docs/s |
|         50th percentile latency | index-append | 392.989 |     ms |
|         90th percentile latency | index-append | 520.343 |     ms |
|         99th percentile latency | index-append | 2059.77 |     ms |
|       99.9th percentile latency | index-append | 2979.19 |     ms |
|      99.99th percentile latency | index-append | 3589.06 |     ms |
|        100th percentile latency | index-append |  3952.6 |     ms |
|    50th percentile service time | index-append | 392.989 |     ms |
|    90th percentile service time | index-append | 520.343 |     ms |
|    99th percentile service time | index-append | 2059.77 |     ms |
|  99.9th percentile service time | index-append | 2979.19 |     ms |
| 99.99th percentile service time | index-append | 3589.06 |     ms |
|   100th percentile service time | index-append |  3952.6 |     ms |
|                      error rate | index-append |       0 |      % |


----------------------------------
[INFO] SUCCESS (took 3340 seconds)
----------------------------------
