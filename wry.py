#!/usr/bin/env python

import tornado.httpserver
import tornado.httpclient
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

import re
_host_exp = re.compile(
    r"(?P<host>.*?)" + 
    r"\.wry\.ly" +
    r"(?P<port>:\d+)?")

_head_exp = re.compile(r"</head>", re.I)

define("port", default=8888, help="run on the given port", type=int)

class WryHandler(tornado.web.RequestHandler):

    def _parse(self):
        m = _host_exp.match(self.request.host)
        return {
            "host": m.group("host"),
            "port": m.group("port") or "",
            "path": "?".join([self.request.path,
                              self.request.query])
        } if m else None

    def _fail_wryly(self):
        self.write("My, my. Aren't we feeling wry?")
        self.finish();

    @tornado.web.asynchronous
    def get(self):
        parsed = self._parse()
        if parsed is None:
            return self._fail_wryly()
        url = "http://%(host)s%(port)s%(path)s" % parsed
        tornado.httpclient.AsyncHTTPClient().fetch(url,
            callback=self.async_callback(self.on_response, url))

    def on_response(self, url, response):
        if response.error:
            return self._fail_wryly()
        ct = response.headers["Content-Type"]
        if "html" in ct:
            self.set_header("Content-Type", ct)
            self.write(re.sub(
                _head_exp,
                "<script src='http://static.wry.ly/frag.js'></script></head>",
                response.body))
        else:
            self.set_status(301)
            self.set_header("Location", url)
        self.finish()

application = tornado.web.Application([
    (r".*", WryHandler),
])

if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
