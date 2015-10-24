from contracts import contract
from contracts.utils import raise_desc, raise_wrapped
from mocdp.comp.interfaces import NamedDP
from mocdp.comp.wrap import SimpleWrap
from mocdp.exceptions import DPSyntaxError
from mocdp.lang.blocks import DPSemanticError
from mocdp.lang.syntax import parse_ndp, parse_wrap
from nose.tools import assert_equal
from comptests.registrar import register_indep
from mocdp.lang.namedtuple_tricks import remove_where_info



def assert_syntax_error(s, expr, desc=None):
    if isinstance(expr, ParsingElement):
        expr = expr.get()
    try:
        res = parse_wrap(expr, s)
    except DPSyntaxError:
        pass
    except BaseException as e:
        msg = "Expected syntax error, got %s." % type(e)
        raise_wrapped(Exception, e, msg, s=s)
    else:
        msg = "Expected an exception, instead succesfull instantiation."
        if desc:
            msg += '\n' + desc
        raise_desc(Exception, msg, s=s, res=res.repr_long())


def assert_semantic_error(s , desc=None):
    """ This asserts that s can be parsed, but cannot  be compiled to a *connected* ndp. """
    try:
        res = parse_ndp(s)
        res.abstract()
    except DPSemanticError:
        pass
    except BaseException as e:
        msg = "Expected semantic error, got %s." % type(e)
        raise_wrapped(Exception, e, msg, s=s)
    else:
        msg = "Expected an exception, instead succesfull instantiation."
        if desc:
            msg += '\n' + desc
        raise_desc(Exception, msg, s=s, res=res.repr_long())

@contract(returns=NamedDP)
def assert_parsable_to_unconnected_ndp(s, desc=None):
    res = parse_ndp(s)
    if res.is_fully_connected():
        msg = 'The graph appears connected but it should be disconnected.'
        raise Exception(msg)
    return res

@contract(returns=NamedDP)
def assert_parsable_to_connected_ndp(s , desc=None):
    """ This asserts that s can be compiled to a *connected* ndp. """
    res = parse_ndp(s)
    if isinstance(res, SimpleWrap):
        return res
    ndp = res.abstract()
    return ndp


@contract(string=str)
def parse_wrap_check(string, expr, result):
    if isinstance(expr, ParsingElement):
        expr = expr.get()

    try:
        res = parse_wrap(expr, string)[0]  # note the 0, first element
        res0 = remove_where_info(res)
        assert_equal(result, res0)
    except BaseException as e:
        msg = 'Cannot parse %r' % string
        raise_wrapped(Exception, e, msg,
                      expr=find_parsing_element(expr),
                      string=string, expected=result)


@contract(string=str)
def parse_wrap_semantic_error(string, expr):
    """ Assert semantic error """
    if isinstance(expr, ParsingElement):
        expr = expr.get()

    try:
        _res = parse_wrap(expr, string)[0]  # note the 0, first element
    except DPSemanticError:
        pass
    except BaseException as e:
        msg = 'Expected DPSemanticError.'
        raise_wrapped(Exception, e, msg,
                      expr=find_parsing_element(expr), string=string)


@contract(string=str)
def parse_wrap_syntax_error(string, expr):
    """ Assert semantic error """
    if isinstance(expr, ParsingElement):
        expr = expr.get()

    try:
        _res = parse_wrap(expr, string)[0]  # note the 0, first element
    except DPSyntaxError:
        pass
    except BaseException as e:
        msg = 'Expected DPSyntaxError.'
        raise_wrapped(Exception, e, msg, expr=find_parsing_element(expr), string=string)


def ok(expr, string, result):
#     job_id = 'parse-%s' % str(string)
#     job_id = None
    expr = find_parsing_element(expr)
    job_id = 'parse-%s-ok' % expr.name
    register_indep(parse_wrap_check, dynamic=False,
                   args=(string, expr, result), kwargs=dict())

def sem(expr, string):
#     job_id = 'parse-%s' % str(string)
#     job_id
#     job_id = None
    expr = find_parsing_element(expr)
    register_indep(parse_wrap_semantic_error, dynamic=False,
                   args=(string, expr), kwargs=dict())

def syn(expr, string):
#     job_id = 'parse-%s' % str(string)
#     job_id = None
    expr = find_parsing_element(expr)
    register_indep(parse_wrap_syntax_error, dynamic=False,
                   args=(string, expr), kwargs=dict())


class ParsingElement():
    def __init__(self, name):
        self.name = name
    def get(self):
        from mocdp.lang.syntax import Syntax
        return getattr(Syntax, self.name)

@contract(returns=ParsingElement)
def find_parsing_element(x):
    from mocdp.lang.syntax import Syntax
    for name, value in Syntax.__dict__.items():  # @UndefinedVariable
        if value is x:
            return ParsingElement(name)
    raise ValueError('Cannot find element for %s.' % str(x))


#         try:
#
#     except DPSemanticError:
#         pass
#     except BaseException as e:
#         msg = "Expected semantic error, got %s." % type(e)
#         raise_wrapped(Exception, e, msg, s=s)
#     else:
#         msg = "Expected an exception, instead succesfull instantiation."
#         if desc:
#             msg += '\n' + desc
#         raise_desc(Exception, msg, s=s, res=res.repr_long())
