from __future__ import unicode_literals

import logging

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
        stream_uri = self.backend.session.get_stream_url(
            track_id, quality=quality)

        logger.info('Translated: %s -> %s', uri, stream_uri)
        self.proxy.set_uri(stream_uri)
        return 'http://localhost:%s' % self.proxy.port
