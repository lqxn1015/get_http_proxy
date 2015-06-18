#!/usr/bin/env python
# -*- coding: utf-8 -*-


from handlers import IndexHandler, RemoveProxyHandler

urls = [
    (r"/", IndexHandler),
    (r"/remove/", RemoveProxyHandler)
]
