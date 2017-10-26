from __future__ import unicode_literals

import logging
import urlparse
import threading

from mopidy import backend

logger = logging.getLogger(__name__)


BITRATES = {
    128: 'low',
    160: 'med',
    320: 'hi',
}


class GMusicPlaybackProvider(backend.PlaybackProvider):

    def __init__(self, audio, backend, proxy):
        super(GMusicPlaybackProvider, self).__init__(audio, backend)
        self.proxy = proxy

    def translate_uri(self, uri):
        track_id = uri.rsplit(':')[-1]

        # TODO Support medium and low bitrate
        quality = BITRATES[self.backend.config['gmusic']['bitrate']]
        #stream_uri = self.backend.session.get_stream_url(
            #track_id, quality=quality)

        def refresh_func():
            stream_uri = self.backend.session.get_stream_url(
                track_id, quality=quality)
            query_string = urlparse.urlsplit(stream_uri).query
            expires_at = int(urlparse.parse_qs(query_string)['expire'].pop())
            return stream_uri, expires_at-2

        uri, expiry = refresh_func()
        
        logger.error("GMusicPlaybackProvider translate_uri in %s", threading.current_thread())
        self.proxy.set_refresh(uri, expiry, refresh_func)
        return 'http://localhost:%s' % self.proxy.port
