from sqlalchemy.engine import reflection, create_engine
from sqlalchemy.sql.schema import MetaData, ForeignKeyConstraint, Table
from sqlalchemy.sql.ddl import DropConstraint, DropTable
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy.ext.declarative.api import declared_attr, has_inherited_table,\
    declarative_base
from collections import OrderedDict
import datetime
import re


_SESSION_EXTENSIONS_ = []
_SESSION_KWARGS_ = {"autoflush": False}
_pool_recycle_ = 60


def overlaps(cls, from_date, to_date):
    '''
        Will check if from_date to_date range overlaps
        cls.from_date cls.to_date range
        returns a sqlqlchemy clause
    '''
    #     return cls.from_date.between(from_date,to_date) |\
    #            cls.to_date.between(from_date,to_date) |\
    #            ((cls.from_date <= from_date) &\
    #             (cls.to_date >= to_date))
    return or_(and_(cls.from_date <= to_date,  # starts
                    cls.from_date >= from_date),
               and_(cls.to_date <= to_date,  # ends
                    cls.to_date >= from_date),
               and_(cls.from_date <= from_date,  # spans
                    cls.to_date >= to_date))


def valid_on(cls, on_date=None):
    '''
        Will check if on_date is within
        cls.from_date cls.to_date range
        returns a sqlqlchemy clause
    '''
    if on_date is None:
        on_date = datetime.datetime.now()
    return and_(cls.valid_from <= on_date,
                or_(cls.valid_to > on_date,
                    cls.valid_to.is_(None)))


def connect(db_url, echo=False, pool_recycle=None):
    '''
        Utility function returns a engine, Session tuple
    '''
    engine = make_engine(db_url, echo, pool_recycle)
    Session = make_session(engine)
    return engine, Session


def make_engine(db_url, echo=False, pool_recycle=None, **kwargs):
    '''
        wrapper for create engine with useful defaults
    '''
    params = dict(echo=echo)
    if 'mysql' in db_url:
        params['encoding'] = 'utf-8'
        params[
            'pool_recycle'] = pool_recycle if pool_recycle else _pool_recycle_
        params['isolation_level'] = 'READ COMMITTED'
    params.update(kwargs)

    engine = create_engine(db_url, **params)
    return engine


def make_session(engine):
    '''
        wrapper from sessionmaker with useful defaults
    '''
    Session = sessionmaker(bind=engine,
                           extension=_SESSION_EXTENSIONS_,
                           **_SESSION_KWARGS_)

    return Session


def create_all(Base, engine):
    '''
        fewer dots
    '''
    Base.metadata.create_all(engine)


def drop_all(session):
    '''
        drops current schema
    '''
    inspector = reflection.Inspector.from_engine(session.bind)

    # gather all data first before dropping anything.
    # some DBs lock after things have been dropped in
    # a transaction.

    metadata = MetaData()

    tbs = []
    all_fks = []

    for table_name in inspector.get_table_names():
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            if not fk['name']:
                continue
            fks.append(
                ForeignKeyConstraint((), (), name=fk['name'])
            )
        t = Table(table_name, metadata, *fks)
        tbs.append(t)
        all_fks.extend(fks)

    for fkc in all_fks:
        session.execute(DropConstraint(fkc))

    for table in tbs:
        session.execute(DropTable(table))

    session.commit()


def serialize(o):
    result = OrderedDict()
    result["_type"] = o.__class__.__name__
    for key in o.__mapper__.c.keys():
        if key[0] != "_":
            result[key] = getattr(o, key)
    return result


def deserialize(o, values):
    assert values.get("_type") == o.__class__.__name__
    for key in o.__mapper__.c.keys():
        if key[0] != "_" and key != "version_id" and key in values:
            setattr(o, key, values[key])


def heroku_db_url(db_url):
    '''
        turns a mysql:// url into a pymsql url
        dropping the reconnect parameter
    '''
    if db_url.startswith("mysql://"):
        db_url = "mysql+pymysql://" + db_url[len("mysql://"):]
        if db_url.endswith("?reconnect=true"):
            db_url = db_url[:-len("?reconnect=true")]
    return db_url


class _Base_(object):
    '''
        This class allows us to base the tablename off the class name.
        We also check for has_inherited_table, so as not to redeclare.
        We make the table name to lower case and underscored.

        We don't implement the primary key in base as some classes will use
        a foreign key to a parent table as their primary key.

        see: http://docs.sqlalchemy.org/en/rel_0_7/orm/extensions/declarative.html#augmenting-the-base
    '''

    @declared_attr
    def __tablename__(self):
        if has_inherited_table(self):
            return None
        name = self.__name__
        return (
            name[0].lower() +
            re.sub(r'([A-Z])', lambda m: "_" + m.group(0).lower(), name[1:])
        )

    __table_args__ = {'mysql_engine': 'InnoDB'}


Base = declarative_base(cls=_Base_)
