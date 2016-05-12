
try:
    from typing import TypeVar

    __builtins__['micro_context'] = TypeVar('micro_context')

except ImportError as ex:
    ''' requires python 3.5 '''
    pass
