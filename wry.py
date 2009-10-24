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

class MainHandler(tornado.web.RequestHandler):

    def _parse(self):
        m = _host_exp.match(self.request.host)
        return {
            "host": m.group("host") + (m.group("port") or ""),
            "slug": m.group("slug"),
            "path": "?".join([self.request.path,
                              self.request.query])
        } if m else None

    @tornado.web.asynchronous
    def get(self):
        parsed = self._parse()
        if parsed is None:
            self.write("My, my. Aren't we feeling wry?")
            self.finish();
            return
        if parsed["slug"] is None:
            pass # TODO
        tornado.httpclient.AsyncHTTPClient().fetch(
            "http://%(host)s%(path)s" % parsed,
            callback=self.async_callback(self.on_response))

    def on_response(self, response):
        if response.error:
            raise tornado.web.HTTPError(500)
        # TODO either find a way to get response headers from pycurl,
        # or switch to httplib2 (probably the latter)
        self.write(response.body)
        self.finish()

application = tornado.web.Application([
    (r".*", MainHandler),
])

if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
