#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import tornado.web

from proxy_data import proxy_data_access


class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        num = int(self.get_argument('num', 10))
        all_proxies = list(proxy_data_access.get_proxies())
        if num < len(all_proxies):
            proxy_list = random.sample(all_proxies, num)
        else:
            proxy_list = all_proxies
        return_dict = dict(proxy_list=proxy_list, all_count=len(all_proxies))
        self.write(json.dumps(return_dict))


class RemoveProxyHandler(tornado.web.RequestHandler):

    def post(self):
        proxy = self.get_argument('proxy', '')
        if proxy:
            proxy_data_access.remove_proxy(proxy)
        self.write('ok')
