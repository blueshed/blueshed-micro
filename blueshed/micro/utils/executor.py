from blueshed.micro.utils import resources
from tornado.concurrent import Future
from tornado.ioloop import IOLoop
from functools import wraps
import logging
import os
import inspect


LOGGER = logging.getLogger(__name__)

_pool_ = None


def pool_init(pool):
    global _pool_
    _pool_ = pool


def global_pool():
    global _pool_
    return _pool_


def register_pool(name, pool):
    resources.set_resource(name, pool)


def has_micro_context(f):
    for k, v in inspect.signature(f).parameters.items():
        if v.annotation == 'micro_context':
            return k


def run_in_pool(_pid, _f, _has_context, context, *args, **kwargs):
    # globals from the parent process in the
    # IOLoop so clear them.
    subprocess = os.getpid() != _pid
    if subprocess and IOLoop.current(False):
        LOGGER.debug("clearing tornado globals")
        IOLoop.clear_current()
        IOLoop.clear_instance()
    LOGGER.debug("running %s %s", os.getpid(), context)
    if _has_context:
        kwargs[_has_context] = context
    result = _f(*args, **kwargs)
    if not subprocess:
        return result
    if isinstance(result, Future):
        LOGGER.debug('running up tornado to complete')

        def done(*args, **kwargs):
            LOGGER.debug('stopping tornado')
            IOLoop.current().stop()
        result.add_done_callback(done)
        IOLoop.current().start()
        result = result.result()
    return context, result


def pool(_f, resource_name=None):
    has_context = has_micro_context(_f)

    @wraps(_f)
    def call(_f, context, *args, **kwargs):
        global _pool_
        if resource_name:
            pool = resources.get_resource(resource_name)
        elif _pool_:
            pool = _pool_
        if pool:
            result = pool.submit(run_in_pool, os.getpid(),  _f,
                                 has_context, context, *args, **kwargs)
        else:
            if has_context:
                kwargs[has_context] = context
            result = _f(*args, **kwargs)
        return result
    return call
