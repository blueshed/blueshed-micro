from tornado.escape import json_decode
from blueshed.micro.utils.json_utils import dumps


class UserMixin(object):
    '''
        Simple mixin to provide utility methods
        to support User
    '''

    @property
    def micro_context(self):
        ''' return the context class declared in application settings'''
        return self.settings.get('micro_context')

    @property
    def cookie_name(self):
        ''' return the cookie_name declared in application settings'''
        return self.settings.get('cookie_name')

    def get_current_user(self):
        ''' return the current user from the cookie '''
        result = self.get_secure_cookie(self.cookie_name)
        if result:
            result = json_decode(result.decode('utf-8'))
        return result

    def set_current_user(self, value):
        ''' put the current user in the cookie '''
        if value:
            self.set_secure_cookie(self.cookie_name, dumps(value))
        else:
            self.clear_cookie(self.cookie_name)
