from blueshed.micro.orm.orm_utils import connect, make_engine
from contextlib import contextmanager
import logging
from sqlalchemy.orm.session import sessionmaker

_session_ = None
_engine_ = None
_binds_ = {}


def db_init(db_url, db_echo=False, db_pool_recycle=None):
    global _session_, _engine_
    _engine_, _session_ = connect(db_url, db_echo, db_pool_recycle)
    logging.info("connecting to: %s", db_url)


def register_db(db_url, models, db_echo=False, db_pool_recycle=None):
    global _session_, _binds_
    if _session_ is None:
        _session_ = sessionmaker()

    engine = make_engine(db_url, db_echo, db_pool_recycle)
    binds = dict([(m, engine) for m in models])
    _binds_.update(binds)
    _session_.configure(binds=_binds_, twophase=True)
    return engine


@contextmanager
def session():
    """Provide a transactional scope around a series of operations."""
    global _session_
    assert _session_
    session = _session_()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
