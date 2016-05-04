'''
    This module allows us to store
    db connections or other
    cross-process resources by name
'''

_resources_ = {}


def set_resource(name, value):
    global _resources_
    _resources_[name] = value


def get_resource(name):
    global _resources_
    try:
        return _resources_.get(name)
    except KeyError:
        raise Exception("Missing resource {}".format(name))
