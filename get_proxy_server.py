#-*- coding: utf-8 -*-
import sys
import signal
import random
import threading
from gevent import monkey
monkey.patch_all()
import requests
import gevent
from bs4 import BeautifulSoup
from gevent.server import StreamServer
import fetchs
import settings
from log import logger

headers = settings.HEADERS



class HttpProxy(object):

    def __init__(self):
        self.init_loader()

    def init_loader(self):
        loader = LoadProxiesHandler()
        if getattr(self,'loader',None):
            self.loader.join()
            external_ip = self.loader.external_ip
            if external_ip :
                loader.external_ip = external_ip
                loader.proxies = self.loader.proxies
                loader.fetchers = self.loader.fetchers
        self.loader = loader
        self.loader.setDaemon(True)

    def get_proxy(self):
        if self.loader.proxies and self.count > 0 :
            return random.choice(self.loader.proxies)
        return ""

    def count(self):
        return len(self.loader.proxies)

    def remove_proxy(self, proxy):
        if proxy in self.loader.proxies:
            self.loader.proxies.remove(proxy)

    def load_proxies(self):
        loader_is_alive = self.loader.isAlive()
        logger.info("isAlive==>%s" % loader_is_alive)
        if not loader_is_alive:
            logger.info("started==>%s" % self.loader.started)
            if self.loader.started:
                self.init_loader()
            self.loader.start()

    def handle(self,socket,address):
        client_request = socket.recv(50)
        if client_request.startswith('get'):
            response = self.get_proxy()
            socket.send(response)
        elif client_request.startswith('count'):
            response = str(self.count())
            socket.send(response)
        elif client_request.startswith('remove'):
            _, proxy = client_request.split("|")
            self.remove_proxy(proxy)
        elif client_request.startswith('reload'):
            self.load_proxies()
        socket.close()


class LoadProxiesHandler(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.started = False
        self.external_ip = ""
        self.proxy_list = []
        self.fetchers = []
        self.proxies = []

    def get_external_ip(self):
        ''' Get the accurate IP '''
        ip = ""
        try:
            resp = requests.get('http://myip.dnsdynamic.org/', headers=headers)
        except:
            resp = requests.get('http://checkmyip.com/', headers=headers)
            text = resp.text
            soup = BeautifulSoup(text)
            ip = soup.find("span", "greentext").get_text().strip()
        else:
            ip = resp.text
        logger.info("external_ip==>%s" % ip)
        self.external_ip = ip

    def regist_fetchs(self):
        get_proxy_fetchs = [_ for _ in dir(fetchs) if isinstance(getattr(fetchs, _), type) and _.lower().endswith('fetch')]
        for fetch in get_proxy_fetchs:
            self.fetchers.append(getattr(fetchs, fetch)())

    def gen_proxy_list(self, fetch):
        self.proxy_list.append(fetch())

    def verify_proxy(self, proxy):
        ''' Run 4 web tests on each proxy IP:port and collect the results '''
        logger.info("proxy==>%s" % proxy)
        proxy = proxy.strip()
        if proxy in self.proxies:
            return
        check_results = []
        urls = ['http://danmcinerney.org/ip.php',
                'http://myip.dnsdynamic.org',
                'http://danmcinerney.org/headers.php']
        http_proxies = {'http': 'http://' + proxy}
        for url in urls:
            try:
                check = requests.get(url,
                                     headers=headers,
                                     proxies=http_proxies,
                                     timeout=15)
                html = check.text
                error = self.__check_verify_resp(html, url)
            except Exception:
                error = True
            check_results.append(error)

        if all(check_results):
            self.proxies.append(proxy)

    def check_verify_resp(self, html, url):
        ''' Check the html for errors and if none are found return time to load page '''
        html_lines = html.splitlines()
        leng = len(html_lines)
        error = False

        # Both of these urls just return the ip and nothing else
        if url in ['http://danmcinerney.org/ip.php', 'http://myip.dnsdynamic.org']:
            if leng == 1:  # Should return 1 line of html
                if self.external_ip in html:
                    error = True
            else:
                error = True

        elif '/headers' in url:
            proxy_headers = ['via: ', 'forwarded: ', 'x-forwarded-for', 'client-ip']
            if leng > 15:  # 15 is arbitrary, I just don't think you'll ever see more than 15 headers
                error = True
            else:
                for l in html_lines:
                    for h in proxy_headers:
                        if h in l.lower():
                            error = True
        return error

    def proxy_checker(self):
        jobs = [gevent.spawn(self.verify_proxy, proxy) for proxy in self.proxy_list]
        try:
            gevent.joinall(jobs)
        except KeyboardInterrupt:
            gevent.killall(jobs)

    def run(self):
        logger.info("run")

        if not self.fetchers:
            self.regist_fetchs()
        jobs = [gevent.spawn(self.gen_proxy_list, f) for f in self.fetchers]
        if not self.external_ip:
            jobs.append(gevent.spawn(self.get_external_ip))
        try:
            logger.info("get_ips")
            gevent.joinall(jobs)
        except KeyboardInterrupt:
            gevent.killall(jobs)

        self.proxy_list = [ips for proxy_site in self.proxy_list for ips in proxy_site]
        self.proxy_list = list(set(self.proxy_list))
        self.proxy_checker()
        self.started = True

def server():
    http_proxy = HttpProxy()
    http_proxy.load_proxies()
    server = StreamServer((settings.PROXY_SERVER_HOST, settings.PROXY_SERVER_PORT), http_proxy.handle)
    server.serve_forever()


def main():
    def handler_exit(signum, frame):
        sys.exit()

    signal.signal(signal.SIGINT, handler_exit)
    signal.signal(signal.SIGTERM, handler_exit)

    server()

if __name__ == '__main__':
    main()
