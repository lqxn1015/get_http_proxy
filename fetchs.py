#-*- coding: utf8 -*-`
import re
import requests
import settings
import bs4
from log import logger


class CheckerProxyFetch(object):
    url = 'http://checkerproxy.net/all_proxy'

    def __call__(self):
        checkerproxy_list = []
        try:
            #http_proxies = {'http': 'http://127.0.0.1:10150'}
            logger.info("get_text_start")
            r = requests.get(self.url, headers=settings.HEADERS, timeout=60)
            logger.info("get_text_end")
            html = r.text
        except Exception, e:
            logger.error(e, exc_info=True)
            return checkerproxy_list
        else:
            soup = bs4.BeautifulSoup(html)
            for tr in soup.find_all('tr'):
                if not tr or len(tr) != 19:
                    continue
                tds = tr.find_all('td')
                proxy_ip = ""
                if tds and len(tds) and tds[3] and tds[3].get_text().strip().lower() == 'http':
                    ip = tds[1].get_text().rstrip().lstrip()
                    logger.info("ip=====>%s" % ip)
                    proxy_status = tds[4].get_text()
                    ip_port = re.match('(\d{1,3}\.){3}\d{1,3}:\d{1,5}', ip)
                    if ip_port:
                        proxy_ip = ip_port.group()
                    if proxy_ip and 'Elite' in proxy_status:
                        checkerproxy_list.append(proxy_ip)
        return checkerproxy_list
