import sys
import traceback

from bs4.element import Tag
from contracts import contract
from contracts.utils import check_isinstance, indent
from mcdp import logger
from mcdp_utils_xml import add_class
from mcdp_utils_xml.parsing import bs

# class to give to the <details> element
ERROR_CLASS = 'error'
WARNING_CLASS = 'warning'


def search_for_errors(soup):
    """
        Returns a string summarizing all errors
        marked by note_error()
    """

    s = ''
    for element in soup.select('details.' + ERROR_CLASS):
        summary = element.summary.text.encode('utf8')
        e2 = element.__copy__()
        e2.summary.extract()
        other = e2.text.encode('utf8')
        s0 = summary + '\n\n' + other
        s += '\n\n' + indent(s0, '', '* ')
    return s


if __name__ == '__main__':
    filename = sys.argv[1]
    data = open(filename).read()
    soup = bs(data)
    s = search_for_errors(soup)
    if s:
        logger.error('Found a few errors:')
        logger.error(s)
    else:
        logger.info('No errors found.')


@contract(long_error='str|$Tag')
def insert_inset(element, short, long_error, klasses=[]):
    """ Inserts an errored details after element """
    details = Tag(name='details')
    summary = Tag(name='summary')
    summary.append(short)
    details.append(summary)
    if isinstance(long_error, Tag):
        pre = Tag(name='div')
    else:
        pre = Tag(name='pre')

    for c in klasses:
        add_class(pre, c)
        add_class(details, c)
        add_class(summary, c)
    pre.append(long_error)
    details.append(pre)

    element0 = element
    while element.next_sibling and element.next_sibling.name == 'details':
        element = element.next_sibling
        add_class(element0, 'contains-consecutive-notes')
        add_class(element, 'consecutive-note')
        add_class(details, 'consecutive-note')

    element.insert_after(details)

    return details


@contract(e=BaseException)
def note_error(tag0, e):
    check_isinstance(e, BaseException)
    add_class(tag0, 'errored')
    short = 'Error'
    long_error = traceback.format_exc(e)
    return insert_inset(tag0, short, long_error, [ERROR_CLASS, type(e).__name__])


@contract(tag0=Tag, msg=bytes)
def note_error_msg(tag0, msg):
    check_isinstance(msg, bytes)
    add_class(tag0, 'errored')
    short = 'Error'
    long_error = msg
    return insert_inset(tag0, short, long_error, [ERROR_CLASS])


@contract(short=str, long_error='str|$Tag')
def note_error2(element, short, long_error, other_classes=[]):
    # if 'errored' in element.attrs.get('class', ''):
    #     return None
    add_class(element, 'errored')
    # logger.error(short + '\n' + long_error)
    inset = insert_inset(element, short, long_error, [ERROR_CLASS] + other_classes)
    parent = element.parent
    if 'style' not in parent.attrs:
        if parent.name != 'blockquote':
            parent.attrs['style'] = 'display: inline;'
    return inset

def note_warning2(element, short, long_error, other_classes=[]):
    logger.warning(short + '\n' + long_error)
    return insert_inset(element, short, long_error, [WARNING_CLASS] + other_classes)
