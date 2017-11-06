import logging
import threading
import time
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.httpclient
import tornado.httputil

client = tornado.httpclient.AsyncHTTPClient(max_clients=1000)
logger = logging.getLogger(__name__)

class ProxyHandler(tornado.web.RequestHandler):

    def initialize(self, stream, event, lock):
        self.stream = stream
        self.track_change = event
        self.lock = lock

    def needs_refresh(self, uri=None, expiry=0, refresh=None):
        now = int(time.time())
        expiry = expiry or now
        return (expiry - now) < 0 and refresh is not None

    def refresh_stream(self, uri=None, expiry=0, refresh=None):
        uri, expiry = refresh()
        return {'uri' : uri, 'expiry' : expiry}

    @tornado.web.asynchronous
    def get(self):
        self.track_change.wait()
        if self.needs_refresh(**self.stream):
            with self.lock:
                self.stream.update(self.refresh_stream(**self.stream))
        uri = self.stream['uri']
        logger.info("Redirect request %s to %s", self.request, uri)
        self.redirect(uri, status=307)


class GmusicProxyServer(threading.Thread):
    
    def __init__(self, port):
        super(GmusicProxyServer, self).__init__()

        self.port = port
        self.data = {}
        self.event = threading.Event()
        self.lock = threading.RLock()

    def run(self):
        app = tornado.web.Application([
            (r'/', ProxyHandler, {'stream' : self.data, 'event' : self.event, 'lock' : self.lock}),
        ])
        server = tornado.httpserver.HTTPServer(app)
        server.listen(self.port)

    def stop(self):
        logger.debug('Stopping HTTP ProxyServer')
        tornado.ioloop.IOLoop.instance().add_callback(
            tornado.ioloop.IOLoop.instance().stop)

    def set_refresh(self, uri, expiry, refresh_func):
        self.event.clear()
        with self.lock:
            self.data.update({'uri' : uri,
                              'expiry' : expiry,
                              'refresh' : refresh_func})
        self.event.set() 
        expires_in = expiry - int(time.time())
        logger.info('%s will expire in %d seconds', uri, expires_in)
