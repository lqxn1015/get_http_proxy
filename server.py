#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import tornado.ioloop
import tornado.web
from tornado.options import options, define

from tasks import WebHttpProxy, RedisHttpProxy
from urls import urls

define("port", default="8888")


class Application(tornado.web.Application):

    def __init__(self, **kwargs):
        tornado.web.Application.__init__(self, **kwargs)
        self.proxy_data_access = kwargs.get('proxy_data_access')


if __name__ == "__main__":
    options.parse_command_line()
    application = Application(
        handlers=urls,
    )
    application.listen(options.port, '0.0.0.0')
    web_proxy = WebHttpProxy()
    redis_proxy = RedisHttpProxy()
    tornado.ioloop.IOLoop.current().add_timeout(
        time.time() + 5,
        web_proxy.get_proxies
    )
    tornado.ioloop.PeriodicCallback(
        web_proxy.get_proxies,
        5 * 60 * 1000
    ).start()  # 5分钟
    tornado.ioloop.PeriodicCallback(
        redis_proxy.get_proxies,
        30 * 60 * 1000
    ).start()  # 30 分钟
    tornado.ioloop.IOLoop.current().start()
