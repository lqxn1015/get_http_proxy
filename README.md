说明
==========
用来获取http代理
------------
服务端
-----
    可以实现自己的fetch,在fetchs.py 里面写fetch class 会自动注册到 server中去抓去 参看CheckerProxyFetch

    runserver:
    python get_proxy_server.py
------------
client
-----
    from get_proxy import GetProxyClient
    client = GetProxyClient()
    proxy = client.get_proxy()
    print proxy
    #if proxy 不可用
    #client.remove_proxy(proxy)避免下次获取到这个不可用的proxy

