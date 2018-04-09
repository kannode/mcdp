# -*- coding: utf-8 -*-
from contracts import contract
from contracts.utils import raise_desc
from mcdp_utils_xml.parsing import to_html_stripping_fragment, bs


@contract(s=bytes, returns=bytes)
def render_markdown(s, fix_blockquote_pre=True):
    """ Returns an HTML string encoded in UTF-8"""
    if isinstance(s, unicode):
        msg = 'I expect utf-8 encoded bytes.'
        raise_desc(TypeError, msg, s=s.__repr__())

    import markdown  # @UnresolvedImport
    import logging
    logging.getLogger("MARKDOWN").setLevel(logging.CRITICAL)

    extensions = [
        'markdown.extensions.smarty',
#         'markdown.extensions.toc',
        'markdown.extensions.attr_list',
        'markdown.extensions.extra',  # need for markdown=1
        'markdown.extensions.fenced_code',
        'markdown.extensions.admonition',
        'markdown.extensions.tables',
    ]

    # markdown takes and returns unicode
    u = unicode(s, 'utf-8')
    html = markdown.markdown(u, extensions)
    html = html.encode('utf-8')

    if fix_blockquote_pre:
        if 'blockquote' in html:
            soup = bs(html)
            for code in soup.select('blockquote > p > code'):
                code.parent.name = 'pre'
            html = to_html_stripping_fragment(soup)
    return html

