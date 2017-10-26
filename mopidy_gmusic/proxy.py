import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.httpclient
import tornado.httputil
import logging
import threading

client = tornado.httpclient.AsyncHTTPClient(max_clients=1000)
logger = logging.getLogger(__name__)

class ProxyHandler(tornado.web.RequestHandler):

    def initialize(self, uri):
        self.uri = uri

    def callback(self, response):
        self.finish()
        #try:
            #self._headers = tornado.httputil.HTTPHeaders() # clear tornado default header
            #for header, v in response.headers.get_all():
                #if header not in ('Content-Length', 'Transfer-Encoding', 'Content-Encoding', 'Connection'):
                    #self.add_header(header, v) # some header appear multiple times, eg 'Set-Cookie'
            #logger.info('got resp: %s status, %s len' % (response.code, len(response.body)))
            #if response.body:
                #self.set_header('Content-Length', len(response.body))
                #self.write(response.body)
        #finally:
            #self.finish()

    def _handle_chunk(self, chunk):
        self.write(chunk)
        self.flush()

    @tornado.web.asynchronous
    def get(self):
        uri = self.uri.get('uri', None)
        if uri is not None:
            req = tornado.httpclient.HTTPRequest(uri, streaming_callback=self._handle_chunk)
            client.fetch(req, self.callback)


class GmusicProxyServer(threading.Thread):
    
    def __init__(self, port):
        super(GmusicProxyServer, self).__init__()

        self.port = port
        self.queue = Queue(1)
        self.uri = {'uri' : None}

    def run(self):
        app = tornado.web.Application([
            (r'/', ProxyHandler, {'uri': self.uri}),
        ])
        server = tornado.httpserver.HTTPServer(app)
        server.listen(self.port)
        tornado.ioloop.IOLoop.current().start()

        logger.debug('Stopped HTTP ProxyServer')

    def stop(self):
        logger.debug('Stopping HTTP ProxyServer')
        tornado.ioloop.IOLoop.instance().add_callback(
            tornado.ioloop.IOLoop.instance().stop)

    def set_uri(self, uri):
        # handle refreshing
        self.uri['uri'] = uri
