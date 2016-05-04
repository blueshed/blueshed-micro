from urllib.parse import urlparse
from tornado.web import HTTPError
from functools import wraps


def cors(f):
    '''
        Wraps GET, POST, PUT, DELETE etc. to allow cross domain requests
        @cors
        def get(self):
            ...
    '''
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        self.write_cors_headers()
        return f(self, *args, **kwargs)
    return wrapped


class CorsMixin(object):
    '''
        This assumes that you're subclassing a websocket / request handler
        Your 'cors_origins' should be a url string list placed in settings.
    '''

    _cors_methods_ = 'GET,POST,PUT,DELETE,OPTIONS'
    _cors_whitelist_ = []

    def set_cors_methods(self, method_string):
        self._cors_methods_ = method_string

    def set_cors_whitelist(self, origins):
        self._cors_whitelist_ = origins

    @property
    def origin_whitelist(self):
        '''get origins from settings or specified whitelist'''
        if self._cors_whitelist_:
            return self._cors_whitelist_

        return self.settings.get('cors_origins')

    @property
    def request_origin(self):
        url = self.request.headers.get("Referer")
        if url:
            o = urlparse(url)
            origin = o.scheme + "://" + o.hostname
            if o.port:
                origin = "{}:{}".format(origin, o.port)
            return origin

    def write_cors_headers(self):
        if self.origin_whitelist and self.request_origin in self.origin_whitelist:
            self.set_header("Access-Control-Allow-Origin", self.request_origin)
            self.set_header('Access-Control-Allow-Credentials', 'true')

    def cors_options(self, *arg, **kwargs):
        if self.origin_whitelist and self.request_origin in self.origin_whitelist:
            self.set_header("Access-Control-Allow-Origin", self.request_origin)
            self.set_header('Access-Control-Allow-Credentials', 'true')
            self.set_header('Access-Control-Allow-Methods', self._cors_methods_)
            self.set_header('Access-Control-Allow-Headers',
                            'Origin, X-Requested-With, Content-Type, Accept, Key, Cache-Control')
            self.set_header('Access-Control-Max-Age', 3000)
            self.set_status(204)
            self.finish()
        else:
            raise HTTPError(403)
