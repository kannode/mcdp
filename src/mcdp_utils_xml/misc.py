from bs4 import Tag, NavigableString
from contracts import check_isinstance, contract


def br():
    t = Tag(name='br')
    t.can_be_empty_element = True
    return t

def soup_find_absolutely(soup, id_):
    """ Finds the element with the given ID, or raise KeyError. """
    e = soup.find(id=id_)
    if e is None:
        msg = 'Cannot find element with ID %r' % id_
        raise KeyError(msg)
    assert e.attrs['id'] == id_
    return e


def copy_contents_into(a, b):
    """ Copy the contents of a into b """
    for e in a.children:
        b.append(e.__copy__())



@contract(text='str|unicode')
def stag(name, text, _class=None, _id=None, href=None):
    """ If text is none, it is replaced by the empty string. """
    check_isinstance(name, (str, unicode))
    check_isinstance(text, (str, unicode))
    if text is None:
        text = ''
    t = Tag(name=name)
    t.append(NavigableString(text))
    if _class is not None:
        t['class'] = _class
    if _id is not None:
        t['id'] = _id

    if href is not None:
        t['href'] = href
    return t
