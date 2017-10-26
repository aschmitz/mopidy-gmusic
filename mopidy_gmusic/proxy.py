import logging
import threading
import time
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.httpclient
import tornado.httputil
import urlparse

client = tornado.httpclient.AsyncHTTPClient(max_clients=1000)
logger = logging.getLogger(__name__)

class ProxyHandler(tornado.web.RequestHandler):

    def initialize(self, stream, refresh, lock):
        self.stream = stream
        self.refresh = refresh
        self.lock = lock
        logger.error("ProxyHandler init in %s has %s", threading.current_thread(), stream)

    def callback(self, response):
        logger.error("Fetch done")
        self.finish()

    def _handle_chunk(self, chunk):
        self.write(chunk)
        self.flush()

    @tornado.web.asynchronous
    def get(self):
        logger.error("ProxyHandler get in %s with %s", threading.current_thread(), self.stream)
        self.refresh.wait()

        now = int(time.time())
        expiry = self.stream.get('expires') or now
        refresh_func = self.stream.get('refresh')
        if (expiry - now) < 0 and refresh_func is not None:
            with self.lock:
                self.stream['uri'], self.stream['expires'] = refresh_func()
            logger.error('Refreshed %s until %d', self.stream['uri'], self.stream['expires'])
        logger.error("Get requst using %s with %s", self.stream['uri'], self.request)
        req = tornado.httpclient.HTTPRequest(self.stream['uri'], streaming_callback=self._handle_chunk)
        client.fetch(req, self.callback)


class GmusicProxyServer(threading.Thread):
    
    def __init__(self, port):
        super(GmusicProxyServer, self).__init__()

        self.port = port
        self.data = {}
        self.refresh = threading.Event()
        self.lock = threading.RLock()

    def run(self):
        app = tornado.web.Application([
            (r'/', ProxyHandler, {'stream' : self.data, 'refresh' : self.refresh, 'lock' : self.lock}),
        ])
        server = tornado.httpserver.HTTPServer(app)
        server.listen(self.port)
        tornado.ioloop.IOLoop.current().start()

        logger.debug('Stopped HTTP ProxyServer')

    def stop(self):
        logger.debug('Stopping HTTP ProxyServer')
        tornado.ioloop.IOLoop.instance().add_callback(
            tornado.ioloop.IOLoop.instance().stop)

    def set_refresh(self, uri, expiry, refresh_func):
        # handle refreshing
        logger.error("GmusicProxyServer set_refresh in %s", threading.current_thread())
        self.refresh.clear()
        with self.lock:
            self.data.update({'uri' : uri,
                              'expires' : expiry,
                              'refresh' : refresh_func})
        self.refresh.set() 
        expires_in = expiry - int(time.time())
        logger.error('%s will expire in %d seconds', uri, expires_in)
        
