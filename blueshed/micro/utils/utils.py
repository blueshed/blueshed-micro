import random
import string
from urllib.parse import urlparse


def url_to_cors(url):
    o = urlparse(url)
    return "{}://{}".format(o.scheme, o.netloc)


def url_to_ws_origins(url):
    o = urlparse(url)
    return o.netloc


def patch_tornado():
    # to provide svg and gzip svg support
    import mimetypes
    import tornado.web

    mimetypes.add_type('image/svg+xml', '.svg')  # because its not there!
    tornado.web.GZipContentEncoding.CONTENT_TYPES.add('image/svg+xml')
    # because its not there!
    mimetypes.add_type('application/font-woff', '.woff')
    # because its not there!
    mimetypes.add_type('application/font-woff2', '.woff2')


def gen_token(length=32):
    return ''.join(random.choice(string.hexdigits) for _ in range(length))
