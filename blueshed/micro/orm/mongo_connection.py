import logging
from urllib.parse import urlparse
from motor.motor_tornado import MotorClient


_client_ = None


def db_init(db_url):
    global _client_
    o = urlparse(db_url)
    client = MotorClient(db_url)
    if o.path:
        ''' warning - this connection is to one database as heroku puts the db into the uri '''
        _client_ = client[o.path[1:]]
    else:
        _client_ = client
    logging.info("connecting to: %s", db_url)


def client():
    global _client_
    return _client_
