from tornado import web
from tornado.escape import json_encode
from tornado.web import HTTPError
from blueshed.micro.utils.json_utils import dumps
from blueshed.micro.web.user_mixin import UserMixin
import logging


LOGGER = logging.getLogger(__name__)


class ContextMixin(UserMixin):
    '''
        Mixin to contain common functionality
        between websocket and request_handler
    '''

    context_clients = []

    @property
    def micro_context(self):
        ''' return the context class declared in application settings'''
        return self.settings.get('micro_context')

    def get_service(self, path):
        if path.startswith("/"):
            path = path[1:]
        if '.' in path:
            path = path.split(".")[0]
        if path:
            service = self.settings['services'].get(path)
            if service is None:
                raise web.HTTPError(400, "no service named {}".format(path))
            return service

    def flush_context(self, context):
        ''' after a success broadcast anything in the context '''
        queue = self.settings.get("broadcast_queue")
        context.flush(self, queue, self.context_clients)
        context.flushed(self)

    def update_result_data(self, context, data):
        LOGGER.debug("current_user %s == %s",
                     self.current_user,
                     context.cookies.get('current_user'))
        if context.cookies.get('current_user') != self.current_user:
            setattr(self, '_current_user', context.cookies.get('current_user'))
            if not hasattr(self, "write_message"):
                self.set_current_user(context.cookies.get('current_user'))
            data['cookie_name'] = self.cookie_name
            data['cookie'] = web.create_signed_value(
                self.settings["cookie_secret"],
                self.cookie_name,
                dumps(self.current_user)).decode("utf-8")

    def handle_future(self, service, context, finish, future):
        ''' called by async repsonses '''
        try:
            result = future.result()
            self.handle_result(service, context, result)
            if finish:
                self.finish()
        except Exception as ex:
            self.write_err(context, ex)
            if finish:
                self.finish()

    def handle_result(self, service, context, result):
        ''' formats result and checks for user '''
        LOGGER.info("%s = %s", service.name, result)
        if isinstance(result, tuple) and isinstance(result[0],
                                                    self.micro_context):
            context, result = result
            LOGGER.info("got context")
        if hasattr(self, "_cookies_"):
            self._cookies_.update(context.cookies)
            # TODO: remove None value keys (cookies)
        self.flush_context(context)
        self.write_result(context, result)

    def write_result(self, context, result):
        """Format a result response."""
        data = {
            'id': context.action_id,
            'action': context.action,
            'result': result,
            'status_code': 200,
            'error': None,
            'message': None,
        }
        self.update_result_data(context, data)

        content = dumps(data)

        if hasattr(self, "write_message"):
            self.write_message(content)
        else:
            self.set_header('content-type', 'application/json; charset=UTF-8')
            self.write(content)

    def write_err(self, context, ex):
        """Format an error response."""
        logging.exception(str(ex))
        is_http = isinstance(ex, HTTPError)
        error = str(ex) if is_http else '500 Internal Server Error'
        code = ex.status_code if is_http else 500
        if is_http:
            message = ex.reason
        elif self.settings.get('allow_exception_messages'):
            message = str(ex)
        else:
            message = "Cripes, an unexpected error!"

        err = json_encode({
            'id': context.action_id,
            'action': context.action,
            'result': None,
            'status_code': code,
            'error': error,
            'message': message,
        })

        # if writing to websocket must use write_message else write
        if hasattr(self, "write_message"):
            self.write_message(err)
        else:
            # set response code and set headers
            self.set_status(code, message)
            self.set_header('content-type', 'application/json; charset=UTF-8')
            self.write(err)
