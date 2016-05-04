from blueshed.micro.orm.orm_utils import serialize
from tests.actions import model


def save_group(context: 'micro_context',
               name: str,
               id: int=None):
    '''
        Adds a group to the database if
        it is not already there, otherwise
        it updates it.
    '''
    with context.session as session:
        if id:
            group = session.query(model.Group).get(id)
            group.name = name
            signal = "group-changed"
        else:
            group = model.Group(name=name)
            signal = "group-added"
            session.add(group)
        session.commit()
        result = serialize(group)
        context.broadcast(signal, result)
        return result
