#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@version: 1.0
@author: allanpan
@license: Apache Licence 
@contact: panjf2000@gmail.com
@site: http://www.python.org
@file: my_handler.py
@time: 2016/5/7 14:36
@tag: 1,2,3
@todo: ...

"""

import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web

from handler import proxy_handler


class MyHandler(proxy_handler.ProxyHandler):
    @staticmethod
    def on_handle_response(self, response):
        # self.request.headers.get("X-Real-Ip",'')
        if response.error and not isinstance(response.error, tornado.httpclient.HTTPError):
            self.set_status(500)
            self.write('Internal server error:\n' + str(response.error))
        elif isinstance(response, tornado.httpclient.HTTPResponse):
            self.set_status(response.code)
            # for header in ('Date', 'Cache-Control', 'Server', 'Content-Type', 'Location'):
            #     v = response.headers.get(header)
            #     if v:
            #         self.set_header(header, v)
            # v = response.headers.get_list('Set-Cookie')
            # if v:
            #     for i in v:
            #         self.add_header('Set-Cookie', i)

            for name, value in response.headers.get_all():
                if name == 'Set-Cookie':
                    self.add_header(name, value)
                else:
                    self.set_header(name, value)

            self.add_header('VIA', 'Toproxy')
            if response.body:
                self.write(response.body)
        self.finish()
