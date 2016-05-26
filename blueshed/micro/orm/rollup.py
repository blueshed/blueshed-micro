from sqlalchemy.sql.expression import ColumnElement, _clause_element_as_expr
from sqlalchemy.ext.compiler import compiles


class rollup(ColumnElement):

    def __init__(self, *elements):
        self.elements = [_clause_element_as_expr(e) for e in elements]


@compiles(rollup, "mysql")
def _mysql_rollup(element, compiler, **kw):
    return "%s WITH ROLLUP" % (', '.join([compiler.process(e, **kw) for e in element.elements]))
