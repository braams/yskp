#!/usr/bin/env python
# -*- coding: utf-8 -*-


from uuid import uuid4
import xml.etree.ElementTree as ET
import logging

from twisted.web.client import getPage
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import endpoints
from twisted.internet import reactor
from twisted.web.server import NOT_DONE_YET

from urllib import urlencode

KEY = "XXXXXXXXXXXXXXXXXXXXXXX"

log = logging.getLogger(__name__)


class ASR(Resource):
    def render_GET(self, request):
        return '<html><body>usage: curl "http://localhost:9757/asr" --data-binary @test.wav</body></html>'

    def _onResponse(self, response, request):
        root = ET.fromstring(response)
        if root.attrib["success"] == "1":
            text = root[0].text.encode('utf8')
            log.info("asr: " + text)
            request.write(text)
        request.finish()

    def _onError(self, error, request):
        request.write('')
        log.error(error)
        request.finish()

    def render_POST(self, request):
        postdata = request.content.read()
        headers = {'Content-Type': 'audio/x-wav'}

        url = 'https://asr.yandex.net/asr_xml?'
        params = {'uuid': uuid4().hex, 'topic': 'queries', 'key': KEY}
        url += urlencode(params)

        d = getPage(url, method='POST', postdata=postdata, headers=headers, timeout=10)

        d.addCallback(self._onResponse, request)
        d.addErrback(self._onError, request)
        return NOT_DONE_YET


class TTS(Resource):
    def render_GET(self, request):
        return '<html><body>usage: curl "http://localhost:9757/tts" --data-binary "некоторый текст на русском языке" -s -o test.wav</body></html>'

    def _onResponse(self, response, request):
        request.setHeader('Content-Type', 'audio/x-wav')
        request.write(response)
        request.finish()

    def _onError(self, error, request):
        log.error(error)
        request.write('')
        request.finish()

    def render_POST(self, request):
        text = request.content.read()
        log.info('tts: ' + text)
        if not text:
            text = ' '

        url = 'https://tts.voicetech.yandex.net/generate?'
        params = {'format': 'wav', 'lang': 'ru-RU', 'speaker': 'zahar', 'emotion': 'neutral', 'quality': 'lo',
                  'key': KEY,
                  'text': text}

        url += urlencode(params)

        d = getPage(url, timeout=10)
        d.addCallback(self._onResponse, request)
        d.addErrback(self._onError, request)
        return NOT_DONE_YET


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    root = Resource()
    root.putChild("asr", ASR())
    root.putChild("tts", TTS())
    factory = Site(root)
    endpoint = endpoints.TCP4ServerEndpoint(reactor, 9757)
    endpoint.listen(factory)
    reactor.run()
