# TODO

- [ ] 为 `--distribution-version` 提供选项 `manticore`， 处理为 manticore 的测试分支

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