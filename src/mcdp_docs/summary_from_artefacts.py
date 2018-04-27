import sys

from bs4 import Tag
from mcdp_docs.sync_from_circle import get_artefacts, get_links_from_artefacts
import os

from mcdp_utils_misc import write_data_to_file


def go(d, out):
    d0 = os.path.dirname(out)
    artefacts = get_artefacts(d0, d)
    print "\n".join(map(str, artefacts))
    links = get_links_from_artefacts(artefacts)

    body = Tag(name='body')
    body.append(links)
    html = Tag(name='html')
    head = Tag(name='head')
    meta = Tag(name='meta')
    meta.attrs['content'] = "text/html; charset=utf-8"
    meta.attrs['http-equiv'] = "Content-Type"
    style = Tag(name='style')
    style.append("""
    body {
        column-count: 3;
    }
    """)
    head.append(meta)

    html.append(head)
    html.append(body)

    write_data_to_file(str(html), out)

if __name__ == '__main__':
    go(sys.argv[1], sys.argv[2])
