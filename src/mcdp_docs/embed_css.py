import os
import sys

from bs4 import BeautifulSoup
from bs4.element import Tag

from compmake.utils import friendly_path

from .logs import logger


def embed_css_files(soup):
    """ Look for <link> elements of CSS and embed them if they are local files"""
    # <link href="..." rel="stylesheet" type="text/css"/>
    for link in list(soup.findAll('link', attrs={'rel':'stylesheet', 'href': True})):
        href = link.attrs['href']
        if href.startswith('file://'):
            filename = href.replace('file://', '')
        elif href.startswith('/'):  # not on windows?
            filename = href
        else:
            filename = None

        if filename is not None:

            if not os.path.exists(filename):
                msg = 'Cannot find CSS file %s' % filename
                logger.error(msg)
                raise Exception(msg)
            else:
                logger.info('Embedding %r' % friendly_path(filename))
                data = open(filename).read()
                style = Tag(name='style')
                style.attrs['type'] = 'text/css'
                style.string = data
                link.replace_with(style)


if __name__ == '__main__':
    logger.info('Loading from stdin...\n')

    contents = sys.stdin.read()
    soup = BeautifulSoup(contents, 'lxml', from_encoding='utf-8')
    embed_css_files(soup)
    contents2 = str(soup)

    if len(sys.argv) >= 2:
        fn = sys.argv[1]
        logger.info('Writing to %s' % fn)
        with open(fn, 'w') as f:
            f.write(contents2)
    else:
        logger.info('Writing to stdout')
        sys.stdout.write(contents2)
