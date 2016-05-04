from blueshed.micro.orm.orm_utils import serialize
from tests.actions import model


def filter_groups(context: 'micro_context', term='',
                  offset=0, limit=10, id=None):
    '''
        returns a list of groups filtered by
        group.name starts with term
    '''
    with context.session as session:
        if id is not None:
            group = session.query(model.Group).get(id)
            result = serialize(group)
            return result
        term = "{}%".format(term)
        groups = session.query(model.Group).\
            filter(model.Group.name.like(term))

        return [serialize(group) for group in groups]
