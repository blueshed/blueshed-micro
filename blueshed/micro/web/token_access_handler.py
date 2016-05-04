from tornado.web import RequestHandler
from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient
from urllib.parse import urlencode
from blueshed.micro.utils.utils import url_to_cors
from tornado.escape import json_decode
from blueshed.micro.web.user_mixin import UserMixin
from blueshed.micro.web.cors_mixin import CorsMixin
import logging


class TokenAccessHandler(UserMixin, CorsMixin, RequestHandler):
    '''
        Validates a token with an auth server and
        puts the result into our access control cookie
        and redirects.
    '''

    def initialize(self, service_token, auth_url):
        self.service_token = service_token
        self.auth_url = auth_url

        # cors options
        self.set_cors_methods('GET,OPTIONS')
        self.set_cors_whitelist([url_to_cors(auth_url)])

    def write_error(self, *args, **kwargs):
        ''' Must override base write error to stop uncaught HTTP errors from clearing CORS headers '''
        self.write_cors_headers()
        RequestHandler.write_error(self, *args, **kwargs)

    def options(self):
        self.cors_options()

    @coroutine
    def get(self):
        self.write_cors_headers()
        token = self.get_argument("v")
        logging.info("auth token %s", token)
        try:
            args = {
                "token": token,
                "service_token": self.service_token
            }
            result = yield AsyncHTTPClient().fetch(self.auth_url,
                                                   method="POST",
                                                   body=urlencode(args))
            logging.info(result.body)
            message = json_decode(result.body)
            user = message["result"]
            self.set_current_user(user)
            self.write({'result': "ok"})
        except Exception as ex:
            logging.exception(ex)
            self.write({"error": str(ex)})
        finally:
            self.finish()
