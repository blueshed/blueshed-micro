'''
Created on Jun 26, 2013

@author: peterb
'''
from sqlalchemy import Column, String, Integer, BigInteger, event
from sqlalchemy.types import LargeBinary
from sqlalchemy.ext.hybrid import hybrid_property
import pickle

dispatcher = None


class CacheItem(object):
    """
    For use with MySQL innodb memcache interface
    """

    id = Column('c1', String(64), primary_key=True)
    _data = Column('c2', LargeBinary(2**23))
    flags = Column('c3', Integer, default=1)
    cas = Column('c4', BigInteger, default=1)
    expires = Column('c5', Integer, default=0)

    @hybrid_property
    def data(self):
        return pickle.loads(self._data)

    @data.setter
    def data(self, value):
        self._data = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def mem_cache_key(cls, id, access_context=None):
        return "@@{}.{}".format(cls.class_key, cls.cache_key(id, access_context))

    @classmethod
    def cache_key(cls, id, access_context=None):
        if access_context and hasattr(access_context, "key"):
            return "{}_{}".format(access_context.key, id)
        return str(id)

    @classmethod
    def update_cache(cls, session, id, value, access_context=None):
        key = cls.cache_key(id, access_context)
        item = session.query(cls).filter(cls.id == key).first()
        if item is None:
            item = cls(id=key)
            session.add(item)
        item.data = value

    @classmethod
    def remove_cache(cls, session, id, access_context=None):
        key = cls.cache_key(id, access_context)
        item = session.query(cls).filter(cls.id == key).first()
        if item:
            session.delete(item)

    @classmethod
    def get_cache(cls, control, id, access_context=None):
        key = cls.mem_cache_key(id, access_context=None)
        return control._get_(key)

    @classmethod
    def init_cache_item(cls, session, db_name):
        params = {
            "name": cls.class_key,
            "table": cls.__tablename__,
            "db": db_name
        }
        rs = list(session.execute(
            'SELECT * from innodb_memcache.containers WHERE name=:name', params))
        if len(rs) == 0:
            session.execute(
                'INSERT INTO innodb_memcache.containers VALUES (:name,:db,:table,"c1","c2","c3","c4","c5","PRIMARY")', params)

    @classmethod
    def attatch_session_listeners(cls, Session):
        ''' Override this to add listeners for Session Events '''
        pass

    @classmethod
    def attatch_object_change_listeners(cls, Session, clazz, view_func, signal=None):
        broadcast_attr = "{}_on_success".format(signal)

        def broadcast_on_success(session, signal, message):
            if session.info.get(broadcast_attr) is None:
                session.info[broadcast_attr] = []
            session.info[broadcast_attr].append((signal, message))

        def _cache_before_flush(session, context, instances):
            for item in session.dirty:
                if isinstance(item, clazz):
                    value = view_func(item)
                    cls.update_cache(
                        session, item.id, value, session.info.get("accl_key"))
                    if signal:
                        broadcast_on_success(
                            session, signal=signal, message=value)
            for item in session.deleted:
                if isinstance(item, clazz):
                    cls.remove_cache(
                        session, item.id, item._serialize, session.info.get("accl_key"))
                    if signal:
                        broadcast_on_success(
                            session, signal=signal, message={"id": -item.id})

        def _cache_after_flush(session, context):
            for item in session.new:
                if isinstance(item, clazz):
                    value = view_func(item)
                    cls.update_cache(
                        session, item.id, value, session.info.get("accl_key"))
                    if signal:
                        broadcast_on_success(
                            session, signal=signal, message=value)

        def _cache_after_rollback(session):
            if session.info.get(broadcast_attr):
                del session.info[broadcast_attr]

        def _cache_after_commit(session):
            if dispatcher is not None:
                for signal, message in session.info.setdefault(broadcast_attr, []):
                    dispatcher.send(signal=signal, sender=cls, message=message)
            del session.info[broadcast_attr]

        event.listen(Session, "before_flush", _cache_before_flush)
        event.listen(Session, "after_flush", _cache_after_flush)
        event.listen(Session, "after_rollback", _cache_after_rollback)
        event.listen(Session, "after_commit", _cache_after_commit)
