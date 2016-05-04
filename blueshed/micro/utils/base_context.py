from blueshed.micro.utils.json_utils import dumps

class BaseContext:
    '''
        Stateful context that can be passed as an argument to function
        by annotating the argument with :micro_context
    '''

    def __init__(self, client_id, action_id, action, cookies=None, handler=None):
        self.client_id = client_id
        self.action_id = action_id
        self.action = action
        self.cookies = cookies if cookies else {}
        self.broadcasts = []

    def broadcast(self, signal, message, accl=None):
        self.broadcasts.append((signal, message, accl))

    def set_cookie(self, key, value=None):
        self.cookies[key] = value

    def get_cookie(self, key, default=None):
        return self.cookies.get(key, default)

    def flush(self, handler, queue, clients):
        ''' after a success broadcast anything in the context '''
        for signal, message, _ in self.broadcasts:
            data = dumps({
                "signal": signal,
                "message": message
            })
            if queue:
                queue.post(data)
            else:
                for client in clients:
                    client.write_message(data)

    def flushed(self, handler=None):
        ''' called when broadcast queue is flushed '''
        pass

    def __repr__(self):
        return "Context({}, {}, {})".format(self.client_id,
                                            self.action_id,
                                            self.action)
