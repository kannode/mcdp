from bs4 import BeautifulSoup
from contracts import contract
from contracts.utils import raise_desc, indent, check_isinstance


def bs(fragment):
    """ Returns the contents wrapped in an element called "fragment".
        Expects fragment as a str in utf-8 """

    check_isinstance(fragment, (str, unicode))

    if isinstance(fragment, unicode):
        fragment = fragment.encode('utf8')
    s = '<fragment>%s</fragment>' % fragment

    parsed = BeautifulSoup(s, 'lxml', from_encoding='utf-8')
    res = parsed.html.body.fragment
    assert res.name == 'fragment'
    return res


def to_html_stripping_fragment(soup):
    """ Returns a string encoded in UTF-8 """
    assert soup.name == 'fragment'
    # Delete all the attrs, otherwise it is not going to look like '<fragment>'
    for k in list(soup.attrs):
        del soup.attrs[k]
    s = str(soup)

    S0 = '<fragment>'
    S1 = '</fragment>'
    if not s.startswith(S0):
        msg = 'Invalid generated fragment; expecting %r.' % S0
        msg += '\n\n' + indent(s, ' | ')
        raise Exception(msg)

    check_html_fragment(s)

    s = s[len(S0):]
    s = s[:-len(S1)]
    return s


def to_html_stripping_fragment_document(soup):
    """ Assumes it is <fragment>XXXX</fragment> and strips the fragments. """
    assert soup.html is not None, str(soup)
    s = str(soup)
    s = s.replace('<fragment>', '')
    s = s.replace('</fragment>', '')
    return s


def check_html_fragment(m, msg=None):
    if '<html>' in m or 'DOCTYPE' in m:
        if msg is None:
            msg2 = ""
        else:
            msg2 = msg + ' '
        msg2 += 'This appears to be a complete document instead of a fragment.'
        raise_desc(ValueError, msg2, m=m)

## Use these for entire documents


@contract(s=str)
def bs_entire_document(s):
    parsed = BeautifulSoup(s, 'lxml', from_encoding='utf-8')
    if parsed.find('body') is None:
        msg = 'The provided string was not an entire document.'
        raise_desc(ValueError, msg, s=s[:200])
    return parsed


def to_html_entire_document(soup):
    return str(soup)


def read_html_doc_from_file(filename):
    """ Reads an entire document from the file """
    with open(filename) as f:
        data = f.read()
    return bs_entire_document(data)


def write_html_doc_to_file(soup, filename, quiet=False):
    from mcdp_utils_misc import write_data_to_file

    html = to_html_entire_document(soup)
    write_data_to_file(html, filename, quiet=quiet)

