from sqlalchemy.sql.sqltypes import Text
from sqlalchemy.types import TypeDecorator
from blueshed.micro.utils.json_utils import dumps, loads


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage::

        JSONEncodedDict()

    """

    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = loads(value)
        return value
