#!/usr/bin/env python
# -*- coding: utf-8 -*-

from redis import StrictRedis

from config import PROXY_HASH_NAME, RDB_ADDRESS


class ProxyDataAccess(object):

    def __init__(self):
        self.redis = StrictRedis.from_url(RDB_ADDRESS)
        self.key_name = PROXY_HASH_NAME

    def get_proxies_count(self):
        return self.redis.scard(self.key_name)

    def get_proxies(self):
        return self.redis.smembers(self.key_name)

    def proxy_saved(self, proxy):
        return self.redis.sismember(self.key_name, proxy)

    def add_proxy(self, proxy):
        self.redis.sadd(self.key_name, proxy)

    def remove_proxy(self, proxy):
        self.redis.srem(self.key_name, proxy)

proxy_data_access = ProxyDataAccess()
