from __future__ import unicode_literals

import logging
import urlparse

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

        def refresh_func():
            stream_uri = self.backend.session.get_stream_url(
                track_id, quality=quality)
            query_string = urlparse.urlsplit(stream_uri).query
            expires_at = int(urlparse.parse_qs(query_string)['expire'].pop())
            logger.info('Refreshed %s until %d', stream_uri, expires_at)
            return stream_uri, expires_at-2

        uri, expiry = refresh_func()
        self.proxy.set_refresh(uri, expiry, refresh_func)
        return 'http://localhost:%s' % self.proxy.port
