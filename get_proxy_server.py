#-*- coding: utf-8 -*-
import sys
import random
from gevent import monkey
monkey.patch_all()
import requests
import gevent
from bs4 import BeautifulSoup
from gevent.server import StreamServer
import fetchs
import settings


headers = settings.HEADERS


class HttpProxy(object):

    def __init__(self, verify=None):
        self.external_ip = self.__external_ip()
        self.proxy_list = []
        self.fetchers = []
        self.proxies = []

    def __external_ip(self):
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
        return ip

    def regist_fetch(self, fetch):
        self.fetchers.append(fetch)

    def get_proxy(self):
        if self.proxies:
            return random.choice(self.proxies)
        return ""

    def remove_proxy(self, proxy):
        if self.proxies and proxy in self.proxies:
            self.proxies.remove(proxy)

    def verify_proxy(self, proxy):
        ''' Run 4 web tests on each proxy IP:port and collect the results '''
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
            sys.exit('[-] Ctrl-C caught, exiting')

    def run(self):
        for f in self.fetchers:
            if callable(f):
                self.proxy_list.append(f())
        self.proxy_list = [ips for proxy_site in self.proxy_list for ips in proxy_site]
        self.proxy_list = list(set(self.proxy_list))
        self.proxy_checker()


def main():
    http_proxy = HttpProxy()
    get_proxy_fetchs = [_ for _ in dir(fetchs) if isinstance(getattr(fetchs, _), type) and _.lower().endswith('fetch')]
    for fetch in get_proxy_fetchs:
        http_proxy.regist_fetch(getattr(fetchs, fetch)())
    http_proxy.run()

    print 'external_ip:%s' % http_proxy.external_ip
    print 'http_proxies_count:%s' % len(http_proxy.proxies)

    def handle(socket, address):
        client_request = socket.recv(100)
        if client_request.startswith('get_proxy'):
            response = http_proxy.get_proxy()
        elif client_request.startswith('remove_proxy'):
            _, proxy = client_request.split("|")
            http_proxy.remove_proxy(proxy)
            response = 'OK'
        socket.send(response)
        socket.close()

    server = StreamServer((settings.PROXY_SERVER_HOST, settings.PROXY_SERVER_PORT), handle)
    server.serve_forever()


if __name__ == '__main__':
    main()
