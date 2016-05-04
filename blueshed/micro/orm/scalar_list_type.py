import sqlalchemy.types as types


class ScalarListType(types.TypeDecorator):
    '''
        Splits a string to list of strings and
        joins a list as comma seperated string.
    '''

    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        return ",".join(value) if value else None

    def process_result_value(self, value, dialect):
        return value.split(",") if value else None

    def copy(self):
        return ScalarListType(self.impl.length)
