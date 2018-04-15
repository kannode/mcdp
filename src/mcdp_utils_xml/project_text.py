from bs4 import BeautifulSoup
from bs4.element import NavigableString

__all__ = [
    'project_html',
    'gettext',
]


def project_html(html):
    doc = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    res = gettext(doc, 0)
    return res


def gettext(element, n=0):
    # print('%d %s element %r' % (n, '  ' * n, element.string))

    if isinstance(element, NavigableString):
        string = element.string
        if string is None:
            return ''
        else:
            return string.encode('utf-8')
    else:
        out = ''
        for child in element.children:
            out += gettext(child, n + 1)

        return out


def gettext_repr(element):
    """
        Return a string that is good for viewing.

        Adds newlines after <p>.
    """
    element = element.__copy__()
    for p in list(element.select('p')):
        p.insert_after('\n\n')
    s = gettext(element)
    s = s.replace('\n\n\n', '\n\n')
    s = s.replace('\n\n\n', '\n\n')
    return s
