from blueshed.micro.orm import db_connection
from blueshed.micro.utils.base_context import BaseContext
from tests.actions import model


class Context(BaseContext):
    """ Extend BaseContext to include a db session """

    @property
    def session(self):
        return db_connection.session()

    def flushed(self, handler=None):
        if self.broadcasts:
            with self.session as session:
                user = handler.current_user
                user_id = user.get("id") if user else None
                for signal, message, accl in self.broadcasts:
                    session.add(model.Log(signal=signal,
                                          message=message,
                                          accl=accl,
                                          created_by=user_id))
                session.commit()
