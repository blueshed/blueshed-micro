from pkg_resources import resource_filename  # @UnresolvedImport
from tornado import web
from tornado.escape import json_decode
from tornado.web import asynchronous, RequestHandler
import tornado.concurrent
from blueshed.micro.utils.json_utils import dumps
from blueshed.micro.web.context_mixin import ContextMixin
from blueshed.micro.web.cors_mixin import CorsMixin, cors
import functools
import logging

acceptable_form_mime_types = [
    "application/x-www-form-urlencoded; charset=UTF-8",
    "application/x-www-form-urlencoded"
]

acceptable_json_mime_types = [
    "application/json; charset=UTF-8",
    "application/json;"
]


class RpcHandler(ContextMixin, CorsMixin, RequestHandler):
    '''
        Calls services in application.settings['services']

        get:
            returns the meta data about a service
            or all services

            suffix .js returns a client control
            javascript object for websocket support

            suffix <service name>.html returns
            an html form to run the service

        post:
            form-encoded or json-encoded input
            result is always json
    '''

    def initialize(self, html_template=None, js_template=None, http_origins=None, ws_url=None):
        RequestHandler.initialize(self)
        self.set_cors_methods("OPTIONS,GET,POST")
        if http_origins:
            self.set_cors_whitelist(http_origins)
        self._html_template = html_template
        self._js_template = js_template
        self._ws_url = ws_url if ws_url else "ws://localhost:8080/websocket"

    def get_template_path(self):
        ''' overrides the template path to use this module '''
        if self._html_template is None and self._js_template is None:
            return resource_filename('blueshed.micro.web', "templates")
        return RequestHandler.get_template_path(self)

    def write_error(self, *args, **kwargs):
        ''' Must override base write error to stop uncaught HTTP errors from clearing CORS headers '''
        self.write_cors_headers()
        RequestHandler.write_error(self, *args, **kwargs)

    def options(self, *args, **kwargs):
        self.cors_options()

    @cors
    def get(self, path=None):
        services = self.get_service(path)
        if services is None:
            services = self.settings['services']
            if path is not None and path.endswith(".js"):
                self.set_header('content-type', 'text/javascript')
                self.render(self._js_template or "api-tmpl.js",
                            services=services.values(),
                            ws_url=self._ws_url)
                return
        elif path is not None and path.endswith(".html"):
            self.render(self._html_template or "service.html",
                        service=services,
                        error=None,
                        result=None)
            return
        self.set_header('content-type', 'application/json; charset=UTF-8')
        self.write(dumps(services, indent=4))

    @asynchronous
    @cors
    def post(self, path):
        content_type = self.request.headers['content-type']
        if content_type in acceptable_json_mime_types:
            kwargs = json_decode(self.request.body)
        elif content_type in acceptable_form_mime_types:
            kwargs = dict([(k, self.get_argument(k))
                           for k in self.request.body_arguments.keys()])
        elif content_type and content_type.startswith("multipart/form-data"):
            kwargs = dict([(k, self.get_argument(k))
                           for k in self.request.body_arguments.keys()])
        else:
            raise web.HTTPError(415, 'content type not supported {}'.format(
                self.request.headers['content-type']))
        service = self.get_service(path)
        service.parse_http_kwargs(kwargs)
        context = self.settings['micro_context'](
            -1, -1, service.name, {"current_user": self.current_user},
            self)
        try:
            logging.info("%s(%r)", service.name, kwargs)
            result = service.perform(context, **kwargs)
            if tornado.concurrent.is_future(result):
                result.add_done_callback(
                    functools.partial(self.handle_future,
                                      service,
                                      context,
                                      True))
            else:
                self.handle_result(service, context, result)
                self.finish()
        except Exception as ex:
            self.write_err(context, ex)
            self.finish()
