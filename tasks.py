#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time
import logging
import functools

import tornado.gen
import tornado.web
import tornado.httpclient
from bs4 import BeautifulSoup


from proxy_data import proxy_data_access
from config import REAL_IP


IP_URL = 'http://1111.ip138.com/ic.asp'
IP_REGEX = re.compile('''(?is)\d+\.\d+\.\d+\.\d+''')
TIME_OUT = 5
CONCURRENT_NUM = 50
MAXPROXY = 5000
USERAGENT = (
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML,'
    ' like Gecko) Chrome/32.0.1700.76 Safari/537.36'
)

HUMAN_HEADERS = {
    'Accept': ('text/html,application/xhtml+xml,application/xml;'
               'q=0.9,image/webp,*/*;q=0.8'),
    'User-Agent': USERAGENT,
    'Accept-Encoding': 'gzip,deflate,sdch'
}

tornado.httpclient.AsyncHTTPClient.configure(
    "tornado.curl_httpclient.CurlAsyncHTTPClient",
    **dict(max_clients=CONCURRENT_NUM)
)
client = tornado.httpclient.AsyncHTTPClient()


def asynchronous_fetch(r, callback):
    def handle_response(response):
        callback(response.body)
    try:
        client.fetch(r, callback=handle_response)
    except Exception, e:
        logging.error(e, exc_info=True)


class HttpProxyValidation(object):

    def __init__(self):
        self.source = ''
        self.callback_num = 0
        self.proxies_num = 0
        self.start_time = 0

    def get_proxies(self):
        raise NotImplementedError()

    def check_proxies(self, proxies):
        self.start_time = time.time()
        for proxy in proxies:
            proxy_host, proxy_port = proxy.split(':')
            request = tornado.httpclient.HTTPRequest(
                IP_URL, headers=HUMAN_HEADERS,
                proxy_host=proxy_host,
                proxy_port=int(proxy_port),
                connect_timeout=TIME_OUT,
                request_timeout=TIME_OUT
            )
            callback = functools.partial(self.ip_check_callback, proxy)
            asynchronous_fetch(request, callback)
            self.proxies_num += 1

    def ip_check_callback(self, proxy, body):
        self.callback_num += 1
        if body:
            ip_result = IP_REGEX.findall(body)
            if ip_result:
                ip = ip_result[0]
            else:
                ip = ''
            if ip and ip != REAL_IP:
                logging.info(proxy)
                if self.source != 'redis':
                    proxy_data_access.add_proxy(proxy)
            else:
                proxy_data_access.remove_proxy(proxy)

        if self.callback_num == self.proxies_num:
            use_time = time.time() - self.start_time
            logging.info('[%s] task finish, use_time:%s s' % (self.source, use_time))
            self.callback_num = 0
            self.proxies_num = 0


class WebHttpProxy(HttpProxyValidation):

    def __init__(self):
        super(WebHttpProxy, self).__init__()
        self.source = 'web'

    def get_proxies(self):
        if proxy_data_access.get_proxies_count() > MAXPROXY:
            logging.info('saved proxy num exceed maxproxy num')
            return
        url = 'http://www.kuaidaili.com/free/inha/'
        request = tornado.httpclient.HTTPRequest(url=url)
        asynchronous_fetch(request, self.get_proxies_callback)

    def get_proxies_callback(self, body):
        if not body:
            return
        try:
            proxies = []
            soup = BeautifulSoup(body)
            for tr in soup.find_all('tr'):
                tds = tr.find_all('td')
                if not tds:
                    continue
                ip = tds[0].get_text().strip()
                port = tds[1].get_text().strip()
                p = '%s:%s' % (ip, port)
                proxies.append(p)
            proxy_redis_dict = proxy_data_access.get_proxies()
            proxies = {proxy for proxy in proxies if proxy not in proxy_redis_dict}
            self.check_proxies(proxies)
        except:
            return


class RedisHttpProxy(HttpProxyValidation):

    def __init__(self):
        super(RedisHttpProxy, self).__init__()
        self.source = 'redis'

    def get_proxies(self):
        proxies = proxy_data_access.get_proxies().keys()
        self.check_proxies(proxies)
