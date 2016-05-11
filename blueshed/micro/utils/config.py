from tornado.options import parse_command_line, parse_config_file, options
import os
import logging


def load_config(path=None):
    '''
        Will read file at path if exists
        Will then read environment variables to override
        Will then parse command line to override
    '''
    if path is not None and os.path.isfile(path):
        logging.info("loading config from %s", path)
        parse_config_file(path)

    for k in options.as_dict():
        ''' danger: access of private variables '''
        value = os.getenv(k)
        if value:
            name = options._normalize_name(k)
            option = options._options.get(name)
            option.parse(value)

    parse_command_line()
