# -*- coding: utf-8 -*-
from .development import mcdp_dev_warning


class MCDPException(Exception):
    pass


class MCDPExceptionWithWhere(MCDPException):

    def __init__(self, error, where=None, stack=None):
        if not isinstance(error, str):
            raise ValueError('Expected string, got %r.' % type(error))

        self.error = error
        self.where = where
        self.stack = stack

        MCDPException.__init__(self, error, where, stack)

    def __str__(self):
        error, where, _stack = self.args
        assert isinstance(error, str), error
        s = ""
#         if False: # we have solved in a different way
#             if stack:
#                 s += '\n' + indent(stack,'S ') + '\n'
        s += error.strip()

        if where is not None:
            from contracts.interface import add_prefix
            ws = where.__str__()
            assert isinstance(ws, str), (ws, type(where))
            s += "\n\n" + add_prefix(ws, ' ')
        return s

    def with_filename(self, filename):
        """ Returns the same exception with reference
            to the given filename. """
        where = _get_where_with_filename(self, filename)
        return type(self)(self.error, where=where, stack=self.stack)


class FormatException(MCDPExceptionWithWhere):
    ''' Data format exception '''


class DPInternalError(MCDPExceptionWithWhere):
    """ Internal consistency errors (not user) """


class DPUserError(MCDPExceptionWithWhere):
    """ User mistake """
    pass


class DPSyntaxError(DPUserError):
    pass


class DPSemanticError(DPUserError):
    pass


class DPNotImplementedError(DPInternalError):
    pass


class DPSemanticErrorNotConnected(DPSemanticError):
    pass


class DPUserAssertion(MCDPExceptionWithWhere):
    """
        Assertion thrown by user using assert_leq, etc.
    """
    pass


def _get_where_with_filename(e, filename):
    where = e.where

    if where is None:
        mcdp_dev_warning('warning, where is None here: %s' % e)
        where = None
    else:
        where = where.with_filename(filename)

    return where

