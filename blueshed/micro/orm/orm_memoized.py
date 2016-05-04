import collections
from sqlalchemy import event
from sqlalchemy.orm.session import Session


class orm_memoized(object):
    """A read-only @property that is only evaluated once.

    Adds a listener so that values are expired
    when the object is part of a flush.

    """

    all_memoized = collections.defaultdict(set)

    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        self.all_memoized[cls].add(self.__name__)
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result


@event.listens_for(Session, "after_flush")
def expire_memoized(session, flush_context):
    """expire all orm_memoized en masse for a given flush"""

    for obj in session.identity_map.values():
        for name in orm_memoized.all_memoized[obj.__class__]:
            obj.__dict__.pop(name, None)


from sqlalchemy import __version__

if __version__ < "0.9.0":
    """Make use of the .info dictionary of Session.

    This is a new feature as of 0.9 which works similarly to the
    .info dictionary of Connection and MapperProperty.

    Here, we apply a simple .info dictionary to the Session class
    for versions of SQLAlchemy prior to 0.9.

    """
    from sqlalchemy import util

    @util.memoized_property
    def info(session):
        return {}

    Session.info = info
