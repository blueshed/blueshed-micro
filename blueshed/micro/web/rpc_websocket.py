from tornado.escape import json_decode
import tornado.websocket
from tornado import concurrent
from blueshed.micro.web.context_mixin import ContextMixin
import logging
import time
import urllib
import functools

LOGGER = logging.getLogger(__name__)


class RpcWebsocket(ContextMixin,
                   tornado.websocket.WebSocketHandler):
    '''
        Calls services in application.settings['services']
    '''

    @classmethod
    def keep_alive(cls):
        ''' used to ping the client '''
        msg = str(time.time()).encode("utf8")
        LOGGER.debug(msg)
        for client in cls.context_clients:
            client.ping(msg)

    @classmethod
    def async_broadcast(cls, message):
        ''' used by piko tool to boradcast from queue '''
        for client in cls.context_clients:
            client.write_message(message)

    def initialize(self, ws_origins=None):
        ''' use the origins to specify cors connections '''
        super().initialize()
        self._origins_ = ws_origins
        self._cookies_ = {}

    def check_origin(self, origin):
        ''' checks the origin is in the origins provided at initialization '''
        if self._origins_:
            parsed_origin = urllib.parse.urlparse(origin)
            LOGGER.debug("websocket %s", parsed_origin)
            return parsed_origin.netloc in self._origins_
        return super().check_origin(origin)

    def open(self, *args, **kwargs):
        ''' called when open and adds to static list of clients '''
        self.context_clients.append(self)
        self._client_id = self.get_argument("client_id", id(self))
        self.set_nodelay(True)
        self._cookies_['current_user'] = self.current_user
        LOGGER.debug("websocket open %s", self._client_id)

    def on_message(self, message):
        ''' handle an rpc calls '''
        data = json_decode(message)
        for id_, action, kwargs in data.get("requests"):
            context = self.micro_context(
                self._client_id, id_, action, self._cookies_, self)
            try:
                LOGGER.info(
                    "%s %s %s %r", id(self),
                    context.action_id,
                    context.action,
                    kwargs)
                service = self.settings["services"].get(context.action)
                if service is None:
                    raise Exception("No such service {}".format(context.action))
                result = service.perform(context, ** kwargs)
                if concurrent.is_future(result):
                    result.add_done_callback(
                        functools.partial(self.handle_future,
                                          service,
                                          context,
                                          False))
                else:
                    self.handle_result(service, context, result)
            except Exception as ex:
                self.write_err(context, ex)

    def on_close(self):
        ''' remove ourselves from the static clients list '''
        self.context_clients.remove(self)
        LOGGER.debug("websocket closed %s", self._client_id)
