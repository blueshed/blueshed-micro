from tornado.ioloop import IOLoop
import time


class Status(object):

    def __init__(self, callback, values=None, timeout=0.1):
        self._items_ = values if values is not None else {}
        self._callback_ = callback
        self._timeout_ = timeout
        self._pending_ = None

    def __getitem__(self, key):
        return self._items_.get(key)

    def __setitem__(self, key, value):
        self._items_[key] = value
        loop = IOLoop.instance()
        if self._pending_ is not None:
            loop.remove_timeout(self._pending_)
        self._pending_ = loop.add_timeout(
            time.time() + self._timeout_, self._do_callback_)

    def _do_callback_(self):
        self._pending_ = None
        self._callback_(self)

    @property
    def items(self):
        return self._items_

    def to_json(self):
        return self._items_

    def __repr__(self):
        return repr(self._items_)
