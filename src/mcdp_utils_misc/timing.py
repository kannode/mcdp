# -*- coding: utf-8 -*-
from contextlib import contextmanager
import logging
import sys
import time

from mcdp.logs import logger_performance

__all__ = [
    'timeit',
    'timeit_wall',
]


@contextmanager
def timeit(desc, minimum=None, logger=None):
    logger = logger or logger_performance
#     logger.debug('timeit %s ...' % desc)
    t0 = time.clock()
    yield
    t1 = time.clock()
    delta = t1 - t0
    if minimum is not None:
        if delta < minimum:
            return
    logger.debug('timeit result: %.2f s (>= %s) for %s' % (delta, minimum, desc))


level = 0


@contextmanager
def timeit_wall(desc, minimum=None, logger=None):
    logger = logger or logger_performance
    global level
    pref = '   ' * level + str(level) + ' timeit'
    stacklevel = 3  # because of contextmanager
    msg0 = ('%s %s ...' % (pref, desc))
    if minimum is None:
        log_wrap(logger, msg0, logging.DEBUG, stacklevel=stacklevel)

    t0 = time.time()
    try:
        level += 1
        yield
    except:
        msg = '%s %s: aborted' % (pref, desc)
        log_wrap(logger, msg, logging.DEBUG, stacklevel=stacklevel)
        raise
    finally:
        level -= 1

    t1 = time.time()
    delta = t1 - t0

    msg = '%s %s: %.2f s (>= %s)' % (pref, desc, delta, minimum)

    if minimum is not None:
        if delta < minimum:
            return
        else:
            log_wrap(logger, msg0, logging.DEBUG, stacklevel=stacklevel)
            log_wrap(logger, msg, logging.DEBUG, stacklevel=stacklevel)
    else:
        log_wrap(logger, msg, logging.DEBUG, stacklevel=stacklevel)


def log_wrap(logger, msg, level, stacklevel=1):
    # copied from warning stdlib, with adding function name
    try:
        caller = sys._getframe(stacklevel)
    except ValueError:
        globals = sys.__dict__  #@ReservedAssignment
        lineno = 1
        func = None
    else:
        globals = caller.f_globals  #@ReservedAssignment
        lineno = caller.f_lineno
        func = caller.f_code.co_name
    if '__name__' in globals:
        module = globals['__name__']
    else:
        module = "<string>"
    filename = globals.get('__file__')
    if filename:
        fnl = filename.lower()
        if fnl.endswith((".pyc", ".pyo")):
            filename = filename[:-1]
    else:
        if module == "__main__":
            try:
                filename = sys.argv[0]
            except AttributeError:
                # embedded interpreters don't have sys.argv, see bug #839151
                filename = '__main__'
        if not filename:
            filename = module
#    exc_info = sys.exc_info()
    exc_info = None
    args = ''
    record = logger.makeRecord(module, level, filename, lineno, msg, args,
                               exc_info=exc_info, func=func)  #, extra=None)
    logger.handle(record)
