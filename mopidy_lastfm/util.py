import collections
import functools
import inspect
import logging

import six
import wrapt

from coloredlogs import ColoredStreamHandler


def makelist(value):
    if not isinstance(value, list):
        if isinstance(value, collections.Iterable):
            if isinstance(value, six.string_types):
                return [value]
            return list(value)
        else:
            return [value]
    return value


def build_log_decorator(log):
    @wrapt.decorator
    def log_enter_function(function, instance, args, kwargs):
        log.debug("Calling {0}".format(function.__name__))
        log.debug("Positional arguments {0}".format(args))
        log.debug("Keyword arguments {0}".format(kwargs))
        try:
            result = function(*args, **kwargs)
        except Exception as e:
            log.debug("{0} raised exception {1}".format(function.__name__, e))
            raise
        log.debug("Call to {0} returned {1}".format(function.__name__, result))
        return result

    return log_enter_function


def makelist_decorator(function):
    @functools.wraps(function)
    def wrapped(arg):
        return function(makelist(arg))

    return wrapped


def enable_logger(log_name, level=logging.DEBUG):
    log = logging.getLogger(log_name)
    handler = ColoredStreamHandler(severity_to_style={'WARNING': dict(color='red')})
    handler.setLevel(level)
    log.setLevel(level)
    log.addHandler(handler)


def segment(iterable, segment_length):
    iterable = iter(iterable)
    if segment_length is None:
        yield iterable
        raise StopIteration
    def yield_length():
        for _ in xrange(segment_length):
            yield iterable.next()
    while True:
        segment = list(yield_length())
        if not segment:
            raise StopIteration
        yield segment


class cached_property(object):
    """Descriptor that caches the result of the first call to resolve its
    contents.
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = self.func(obj)
        setattr(obj, self.func.__name__, value)
        return value

    def bust_self(self, obj):
        """Remove the value that is being stored on `obj` for this
        :class:`.cached_property`
        object.

        :param obj: The instance on which to bust the cache.
        """
        if self.func.__name__ in obj.__dict__:
            delattr(obj, self.func.__name__)

    @classmethod
    def bust_caches(cls, obj, excludes=()):
        """Bust the cache for all :class:`.cached_property` objects on `obj`

        :param obj: The instance on which to bust the caches.
        """
        for name, _ in cls.get_cached_properties(obj):
            if name in obj.__dict__ and not name in excludes:
                delattr(obj, name)

    @classmethod
    def get_cached_properties(cls, obj):
        return inspect.getmembers(type(obj), lambda x: isinstance(x, cls))
