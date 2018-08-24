from bs4 import Tag, NavigableString
from contracts import check_isinstance, contract

def get_parents_names(x):
    names = []
    parent = x.parent
    while parent:
        names.append(parent.name)
        parent = parent.parent
    return names


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

def copy_contents_into_beginning(a, b):
    """ Copy the contents of a into b """
    for i, e in enumerate(a.children):
        b.insert(i, e.__copy__())



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

def get_minimal_html_document(title=None, stylesheet=None):
    html = Tag(name='html')
    html.append('\n')
    head = Tag(name='head')
    head.append('\n')
    if stylesheet:
        link = Tag(name='link')
        link.attrs['type'] = 'text/css'
        link.attrs['rel'] = 'stylesheet'
        link.attrs['href'] = stylesheet
        head.append(link)
        head.append('\n')

    meta = Tag(name='meta', attrs={'http-equiv': "Content-Type",
                                        'content': "application/xhtml+xml; charset=utf-8"})
    head.append(meta)
    head.append('\n')
    if title:
        title_t = Tag(name='title')
        title_t.append(title)
        head.append(title_t)
    head.append('\n')
    html.append(head)

    body = Tag(name='body')
    body.append('\n')
    html.append(body)
    return html
