#-*- coding: utf8 -*-
import socket
import settings


class GetProxyClient(object):

    def _request(self, value):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((settings.PROXY_SERVER_HOST, settings.PROXY_SERVER_PORT))
        response = ''
        try:
            sock.send(value)
            sock.settimeout(5)
            response = sock.recv(25)
        except Exception, e:
            raise e
        finally:
            sock.close()
        return response

    def get_proxy(self):
        return self._request('get')

    def count(self):
        return self._request('count')

    def reload(self):
        return self._request('reload')

    def remove_proxy(self, proxy):
        return self._request('remove|%s' % proxy)


if __name__ == '__main__':
    client = GetProxyClient()
    proxy = client.get_proxy()
    count = client.count()
    print proxy,count
    client.reload()
