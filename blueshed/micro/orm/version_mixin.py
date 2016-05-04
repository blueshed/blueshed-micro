from sqlalchemy.types import Integer, DateTime
from sqlalchemy.schema import Column
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.session import Session
from sqlalchemy import event
import datetime


class VersionMixin(object):
    '''
        Mixin to provide version checking on updates
    '''

    version_id = Column(Integer, nullable=False)
    last_updated = Column(DateTime,
                          default=datetime.datetime.now,
                          onupdate=datetime.datetime.now)
    version_by = Column(Integer)

    @declared_attr
    def __mapper_args__(cls):
        return {
            "version_id_col": cls.version_id
        }


def set_version_by(obj, user_id):
    if isinstance(obj, VersionMixin):
        obj.version_by = user_id


@event.listens_for(Session, 'before_flush')
def before_flush(session, flush_context, instances):
    user_id = session.info.get('user_id')
    for obj in session.new:
        set_version_by(obj, user_id)
    for obj in session.dirty:
        set_version_by(obj, user_id)
