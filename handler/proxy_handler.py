#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@version: 1.0
@author: allanpan
@license: Apache Licence 
@contact: panjf2000@gmail.com
@site: http://www.python.org
@file: proxy_handler.py
@time: 2016/5/7 12:06
@tag: 1,2,3
@todo: ...

"""
import os
import socket
import json
import re
import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
from tornado.httputil import HTTPServerRequest
from urlparse import urlparse


def is_json(json_str):
    try:
        json_object = json.loads(json_str)
    except ValueError as e:
        raise e
        return False, {}
    return True, json_object


def get_proxy(url):
    url_parsed = urlparse(url, scheme='http')
    proxy_key = '%s_proxy' % url_parsed.scheme
    print 'proxy_key is %s' % proxy_key
    return os.environ.get(proxy_key)


def base_auth_valid(auth_header, base_auth_user, base_auth_passwd):
    # Basic Zm9vOmJhcg==
    auth_mode, auth_base64 = auth_header.split(' ', 1)
    assert auth_mode == 'Basic'
    # 'Zm9vOmJhcg==' == base64("foo:bar")
    auth_username, auth_password = auth_base64.decode('base64').split(':', 1)
    if auth_username == base_auth_user and auth_password == base_auth_passwd:
        return True
    else:
        return False


def parse_proxy(proxy):
    proxy_parsed = urlparse(proxy, scheme='http')
    return proxy_parsed.hostname, proxy_parsed.port


def match_white_iplist(clientip, white_iplist):
    if clientip in white_iplist:
        return True
    if not white_iplist:
        return True
    return False


def shield_attack(header):
    if re.search(header, 'ApacheBench'):
        return True
    return False


def fetch_request(request, t_port, callback, **kwargs):
    # proxy = get_proxy(url)
    # print 'proxy is %s' % proxy
    # global t_port
    if request and isinstance(request, HTTPServerRequest):
        # logger.debug('Forward request via upstream proxy %s', proxy)
        tornado.httpclient.AsyncHTTPClient.configure(
            'tornado.curl_httpclient.CurlAsyncHTTPClient')
        # host, port = parse_proxy(proxy)
        protocol = request.protocol
        port_index = request.host.index(':')
        host = request.host[:port_index]
        # port = t_port
        port = '' if t_port == 80 else ":%s" % t_port
        uri = request.uri
        url = '%s://%s%s%s' % (protocol, host, port, uri)
        # kwargs['proxy_host'] = host
        # kwargs['proxy_port'] = options.port

        req = tornado.httpclient.HTTPRequest(url, **kwargs)
        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch(req, callback, follow_redirects=True, max_redirects=3)


class ProxyHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'CONNECT']
    set_port = 80
    set_user = ''
    set_pwd = ''
    set_white_iplist = ''

    @classmethod
    def set_static_args(cls, port, user, passwd, white_iplist, on_response=None):
        cls.set_port = port
        cls.set_user = user
        cls.set_pwd = passwd
        cls.set_white_iplist = white_iplist
        cls.func_response = on_response

    @tornado.web.asynchronous
    def __on_handle_response(self, response):
        ProxyHandler.func_response(self, response)

    @tornado.web.asynchronous
    def get(self):

        if self.set_user:
            auth_header = self.request.headers.get('Authorization', '')
            if not base_auth_valid(auth_header, self.set_user, self.set_pwd):
                self.set_status(403)
                self.write('Auth Faild')
                self.finish()
                return

        user_agent = self.request.headers.get('User-Agent', '')
        if shield_attack(user_agent):
            self.set_status(500)
            self.write('andy')
            self.finish()
            return

        client_ip = self.request.remote_ip
        if not match_white_iplist(client_ip, self.set_white_iplist):
            self.set_status(403)
            self.write('')
            self.finish()
            return
        body = self.request.body
        if not body:
            body = None
        on_handle_response = self.__on_handle_response
        try:
            fetch_request(
                self.request, self.set_port, on_handle_response,
                method=self.request.method, body=body,
                headers=self.request.headers, follow_redirects=False,
                allow_nonstandard_methods=True)
        except tornado.httpclient.HTTPError as e:
            if hasattr(e, 'response') and e.response:
                on_handle_response(e.response)
            else:
                self.set_status(500)
                self.write('Internal server error:\n' + str(e))
                self.finish()

    @tornado.web.asynchronous
    def post(self):
        return self.get()

    @tornado.web.asynchronous
    def put(self, *args, **kwargs):
        return self.get()

    @tornado.web.asynchronous
    def connect(self):
        host, port = self.request.uri.split(':')
        client = self.request.connection.stream

        def read_from_client(data):
            upstream.write(data)

        def read_from_upstream(data):
            client.write(data)

        def client_close(data=None):
            if upstream.closed():
                return
            if data:
                upstream.write(data)
            upstream.close()

        def upstream_close(data=None):
            if client.closed():
                return
            if data:
                client.write(data)
            client.close()

        def start_tunnel():
            client.read_until_close(client_close, read_from_client)
            upstream.read_until_close(upstream_close, read_from_upstream)
            client.write(b'HTTP/1.0 200 Connection established\r\n\r\n')

        def on_proxy_response(data=None):
            if data:
                first_line = data.splitlines()[0]
                http_v, status, text = first_line.split(None, 2)
                if int(status) == 200:
                    start_tunnel()
                    return

            self.set_status(500)
            self.finish()

        def start_proxy_tunnel():
            # upstream.write('Server: Toproxy\r\n')
            upstream.write('CONNECT %s HTTP/1.1\r\n' % self.request.uri)
            upstream.write('Host: %s\r\n' % self.request.uri)
            upstream.write('Proxy-Connection: Keep-Alive\r\n\r\n')
            upstream.read_until('\r\n\r\n', on_proxy_response)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        upstream = tornado.iostream.IOStream(s)

        proxy = get_proxy(self.request.uri)
        if proxy:
            proxy_host, proxy_port = parse_proxy(proxy)
            upstream.connect((proxy_host, proxy_port), start_proxy_tunnel)
        else:
            upstream.connect((host, int(port)), start_tunnel)
