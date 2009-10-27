#!/usr/bin/env python

import tornado.httpserver
import tornado.httpclient
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

from settings import SUFFIX, SLUG_EXP

import re
_host_exp = re.compile(
    r"(?P<host>.*?)" + 
    r"(?:\.(?P<slug>" + SLUG_EXP + r"))?" +
    r"\." + SUFFIX +
    r"(?P<port>:\d+)?")

define("port", default=8888, help="run on the given port", type=int)

class WryHandler(tornado.web.RequestHandler):

    def _parse(self):
        m = _host_exp.match(self.request.host)
        return {
            "host": m.group("host") + (m.group("port") or ""),
            "slug": m.group("slug"),
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
        if parsed["slug"] is None:
            pass # TODO
        tornado.httpclient.AsyncHTTPClient().fetch(
            "http://%(host)s%(path)s" % parsed,
            callback=self.async_callback(self.on_response))

    def on_response(self, response):
        if response.error:
            return self._fail_wryly()
        self.set_header("Content-Type", 
                        response.headers["Content-Type"])
        self.write(response.body)
        self.finish()

application = tornado.web.Application([
    (r".*", WryHandler),
])

if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
