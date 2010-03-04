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
    r"(?P<port>:\d+)?",
    re.IGNORECASE)

_head_exp = re.compile(
    r"<head.*?>", 
    re.IGNORECASE | 
    re.MULTILINE |
    re.DOTALL)

define("port", default=8888, help="run on the given port", type=int)

_subdomain = "dev"
define("subdomain", default=_subdomain,
       help="the subdomain of wry.ly from which to load JavaScript",
       type=str)

def html_to_inject(base, subdomain=_subdomain):
    return """
<script src="http://%(subdomain)s.wry.ly/js/loader.js"
        require="http://%(subdomain)s.wry.ly/js#wry/banter">
</script>
<base href="%(base)s" />""" % locals()

class WryHandler(tornado.web.RequestHandler):

    def _parse(self):
        m = _host_exp.match(self.request.host)
        q = self.request.query
        q = q and ("?" + q)
        return {
            "host": m.group("host"),
            "port": m.group("port") or "",
            "path": self.request.path + q
        } if m else None

    def _fail_wryly(self):
        self.write("My, my. Aren't we feeling wry?")
        self.finish();

    def _redirect(self, url):
        self.set_status(301)
        self.set_header("Location", url)
        self.finish()

    def _should_fetch(self):
        hdrs = self.request.headers
        if "Accept" not in hdrs:
            return True # accepts anything
        preferred = hdrs["Accept"].split(";")[0].lower()
        return ("html" in preferred or
                "xml" in preferred or
                "text/*" in preferred or
                "*/*" in preferred or
                not preferred.strip())

    @tornado.web.asynchronous
    def get(self):
        parsed = self._parse()
        if parsed is None:
            return self._fail_wryly()
        #url = "http://%(host)s%(port)s%(path)s" % parsed
        url = "http://%(host)s%(path)s" % parsed # ignore port
        # TODO handle .js requests that depend on Referer header
        # TODO always request urls that have query strings?
        if self._should_fetch():
            # print "referer: ", url
            tornado.httpclient.AsyncHTTPClient().fetch(url,
                callback=self.async_callback(self.on_response, url))
        else:
            self._redirect(url)

    def on_response(self, url, response):
        if response.error:
            return self._fail_wryly()
        try:
            ct = response.headers["Content-Type"].lower()
        except:
            ct = "text/html"
        if "html" in ct:
            self.set_header("Content-Type", ct)
            self.write(re.sub(
                _head_exp,
                "\g<0>" + html_to_inject(url),
                response.body))
            self.finish()
        else:
            self._redirect(url)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    _subdomain = str(options.subdomain)

    tornado.httpserver.HTTPServer(tornado.web.Application([
        (r".*", WryHandler),
    ])).listen(options.port)

    tornado.ioloop.IOLoop.instance().start()
