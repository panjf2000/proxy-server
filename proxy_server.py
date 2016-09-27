# coding:utf-8
# !/usr/bin/env python
import json
import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
from handler import proxy_handler
from custom_handler import my_handler


def read_conf(path=''):
    global config
    with open(path, 'r') as f:
        content = f.read()
        config = json.loads(content)


def run_proxy(port=8888, handler=proxy_handler.ProxyHandler, start_ioloop=True):
    app = tornado.web.Application([
        (r'.*', handler),
    ])
    app.listen(port)
    ioloop = tornado.ioloop.IOLoop.instance()
    if start_ioloop:
        ioloop.start()


if __name__ == '__main__':

    config = dict()
    read_conf('config.json')
    print ("Start a HTTP proxy on port %d" % config.get('port', 80))
    proxy_handler.ProxyHandler.set_static_args(config['proxy_pass'], config.get('mode', 0), config['auth'],
                                               config['user'].get('name', ''),
                                               config['user'].get('passwd', ''), config['white_iplist'],
                                               my_handler.MyHandler.on_handle_response)
    run_proxy(port=config['port'], handler=proxy_handler.ProxyHandler)
