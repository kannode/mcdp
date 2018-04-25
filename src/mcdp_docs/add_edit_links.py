# -*- coding: utf-8 -*-
import sys

from bs4 import BeautifulSoup
from bs4.element import Tag
from mcdp_docs.manual_constants import MCDPManualConstants

from .logs import logger


def add_github_links_if_edit_url(soup, permalink_prefix=None):
    """ 
        If an element has an attribute 'github-edit-url' then add little icons.
    
    """
    attname = MCDPManualConstants.ATTR_GITHUB_EDIT_URL
    nfound = 0

    for h in soup.findAll(MCDPManualConstants.headers_for_edit_links, attrs={attname: True}):
        nfound += 1
        s = Tag(name='span')
        a = Tag(name='a')
        a.attrs['href'] = h.attrs[attname]
        a.attrs['class'] = 'github-edit-link'
        a.attrs['title'] = "Click this link to directly edit on the repository."
        a.string = '✎'
        s.append(a)

        a = Tag(name='a')
        hid = h.attrs['id']
        if hid is not None:
            if ':' in hid:
                hid = hid[hid.index(':') + 1:]
            if permalink_prefix is not None:
                if not 'autoid' in hid:
                    url = permalink_prefix + str(hid)
                    a.attrs['href'] = url
                    a.string = '🔗'
                    a.attrs['class'] = 'purl-link'
                    a.attrs['title'] = "Use this link as the permanent link to share with people."
                    s.append(a)

        s.attrs['class'] = 'github-etc-links'
        h.insert_after(s)

    logger.info('Found %d elements with attribute %r' % (nfound, attname))



def go():
    sys.stderr.write('Loading from stdin...\n')

    contents = sys.stdin.read()
    #     print ('start: %s  ... %s' % (contents[:100], contents[-100:]))
    soup = BeautifulSoup(contents, 'lxml', from_encoding='utf-8')
    #     soup = bs(contents)
    #     print 'soup: %s' % soup
    # ssoup = str(soup)
    #     print ('\n\nstart: %s  ... %s' % (ssoup[:100], ssoup[-100:]))

    permalink_prefix = 'http://purl.org/dth/'
    add_github_links_if_edit_url(soup, permalink_prefix)
    #     print(str(soup)[:0])

    contents2 = str(soup)

    if len(sys.argv) >= 2:
        fn = sys.argv[1]
        sys.stderr.write('Writing to %s\n' % fn)
        with open(fn, 'w') as f:
            f.write(contents2)
    else:
        sys.stderr.write('Writing to stdout\n')
        sys.stdout.write(contents2)


if __name__ == '__main__':
    go()
