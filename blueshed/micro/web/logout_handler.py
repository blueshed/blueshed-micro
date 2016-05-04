import tornado.web


class LogoutHandler(tornado.web.RequestHandler):
    '''
        Removes the cookie from application settings
        and redirects.
    '''

    @property
    def cookie_name(self):
        return self.application.settings.get('cookie_name')

    def get(self):
        ''' removes cookie and redirects to optional next argument '''
        self.clear_cookie(self.cookie_name)
        self.redirect(self.get_argument("next", "/"))
