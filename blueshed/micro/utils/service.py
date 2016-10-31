from collections import OrderedDict
import inspect
import logging
from tornado.ioloop import IOLoop
import os
from blueshed.micro.utils import executor
from functools import wraps

LOGGER = logging.getLogger(__name__)


def no_pool(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return f(*args, ** kwargs)

    setattr(wrapped, "_no_pool_", True)
    return wrapped


class Service(object):
    '''
       Wraps a function with a description so that it can be
       called synchronously or asynchronously
    '''

    def __init__(self, key, f):
        self.name = key
        self.label = key.replace("_", " ")
        self.desc = inspect.signature(f)
        self.docs = inspect.getdoc(f)
        self.no_pool = hasattr(f, '_no_pool_')
        self.f = f
        self.has_context = None
        for k, v in self.desc.parameters.items():
            if v.annotation == 'micro_context':
                self.has_context = k
                break

    def __str__(self):
        return "%s %s - %s" % (self.name, self.desc, self.docs)

    @classmethod
    def describe(cls, target):
        '''
            Will dir target and inspect each
            function and return an instance of
            this class for each

            functions starting with '_' are ignored
        '''
        result = OrderedDict()
        for key in filter(lambda x: x[0] != '_', dir(target)):
            f = getattr(target, key)
            if inspect.isfunction(f):
                s = cls(key, f)
                LOGGER.info(s)
                result[key] = s
        return result

    def perform(self, context, **kwargs):
        '''
            Call synchronously
        '''
        if executor.global_pool() and self.no_pool is not True:
            return self.perform_in_pool(executor.global_pool(),
                                        context,
                                        **kwargs)
        else:
            if self.has_context:
                kwargs[self.has_context] = context
            return self.f(**kwargs)

    def perform_in_pool(self, pool, context, **kwargs):
        '''
            Call with a process pool executor
        '''
        logging.info("run %s %s", os.getpid(), context)
        logging.info(IOLoop.current(False))
        return pool.submit(executor.run_in_pool,
                           os.getpid(),
                           self.f,
                           self.has_context,
                           context,
                           **kwargs)

    def parse_http_kwargs(self, values):
        '''
            type conversion for int and float args
        '''
        params = self.desc.parameters.items()
        for k, v in values.items():
            if k in params and v is not None:
                if params[k].annotation is int:
                    values[k] = int(v)
                if params[k].annotation is float:
                    values[k] = float(v)

    @classmethod
    def annotation_to_str(cls, annotation):
        if annotation is None:
            return None
        if isinstance(annotation, str):
            return annotation
        if issubclass(annotation, object):
            return annotation.__name__
        return annotation

    @property
    def has_files(self):
        '''
            returns True if a parameter has as annotation 'file'
        '''
        for param in self.desc.parameters.values():
            if param.annotation == 'file':
                return True

    def to_json(self):
        ''' so it can be dumped '''
        return OrderedDict([
            ("name", self.name),
            ("params", [str(p) for p in self.desc.parameters.values()]),
            ("returns", self.annotation_to_str(self.desc.return_annotation)
             if self.desc.return_annotation is not self.desc.empty else ""),
            ("has_files", self.has_files),
            ("docs", self.docs)
        ])
