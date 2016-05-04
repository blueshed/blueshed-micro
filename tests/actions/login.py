from tests.actions import model


def login(context: 'micro_context', email: str, password: str) -> dict:
    ''' returns a user object on success '''
    with context.session as session:
        person = session.query(model.User).\
            filter(model.User.email == email,
                   model.User.password == password).\
            first()
        if person is None:
            raise Exception(
                "<strong>Failed</strong> Email or password incorrect!")
        user = {
            "id": person.id,
            "email": person.email,
            "name": person.name
        }
        context.set_cookie("current_user", user)
        return user
