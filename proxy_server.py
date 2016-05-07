# coding:utf-8
# !/usr/bin/env python

import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
from handler import proxy_handler
from custom_handler import my_handler


def run_proxy(port=8888, handler=proxy_handler.ProxyHandler, start_ioloop=True):
    app = tornado.web.Application([
        (r'.*', handler),
    ])
    app.listen(port)
    ioloop = tornado.ioloop.IOLoop.instance()
    if start_ioloop:
        ioloop.start()


if __name__ == '__main__':
    white_iplist = []
    import argparse

    parser = argparse.ArgumentParser(
        description='''python proxy_server.py -p 8080 -tp 80 ''')

    parser.add_argument('-p', '--port', help='tonado proxy listen port', action='store', default=8080)
    parser.add_argument('-tp', '--t_port', help='the real port', action='store', default=8000)
    parser.add_argument('-w', '--white', help='white ip list ---> 127.0.0.1', action='store', default=[])
    parser.add_argument('-u', '--user', help='Base Auth, like xiaoming:123123', action='store', default=None)
    args = parser.parse_args()
    if not args.port:
        parser.print_help()
    port = int(args.port)
    if not args.t_port:
        parser.print_help()

    t_port = int(args.t_port)
    white_iplist = args.white
    if args.user:
        base_auth_user, base_auth_passwd = args.user.split(':')
    else:
        base_auth_user, base_auth_passwd = None, None

    print ("Start a HTTP proxy on port %d" % port)
    proxy_handler.ProxyHandler.set_static_args(t_port, base_auth_user, base_auth_passwd, white_iplist,
                                               my_handler.MyHandler.on_handle_response)
    run_proxy(port=port, handler=proxy_handler.ProxyHandler)
    # run_proxy(port=port, handler=my_handler.MyHandler)
