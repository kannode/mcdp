import os

from bs4 import BeautifulSoup

from compmake.utils.safe_write import write_data_to_file
from comptests.registrar import run_module_tests, comptest
from mcdp_docs.manual_join_imp import manual_join, split_in_files, \
    add_prev_next_links, update_refs, get_id2filename, create_link_base, \
    DocToJoin
from mcdp_docs.pipeline import render_complete
from mcdp_library.library import MCDPLibrary
from mcdp_tests import logger


@comptest
def document_split():
    html = get_split_test_document(test_md)
    soup = BeautifulSoup(html, 'lxml')
    for e in soup.select('.toc'):
        e.extract()
    html = soup.prettify()
    fn = 'out/document_split.html'
    with open(fn, 'w') as f:
        f.write(html)
    logger.info('written on %s' % fn)

    filename2contents = split_in_files(soup)
    id2filename = get_id2filename(filename2contents)
    add_prev_next_links(filename2contents)
    update_refs(filename2contents, id2filename)

    linkbase = 'link.html'
    filename2contents[linkbase] = create_link_base(id2filename)

#     d = 'out/sec'
#     write_split_files(filename2contents, d)

#     print html


def get_split_test_document(s):
    library = MCDPLibrary()
    realpath = 'internal'
    raise_errors = True
    rendered = render_complete(library=library, s=s, raise_errors=raise_errors,
                               realpath=realpath, generate_pdf=False,
                               check_refs=True, filter_soup=None)

    files_contents = [DocToJoin(docname='unused', source_info=None, contents=rendered)]
    stylesheet = None
    template = """<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        </head>
        <style>

        </style>
        <body></body></html>
        """
    complete_aug = manual_join(template=template,
                            files_contents=files_contents,
                            stylesheet=stylesheet, remove=None, extra_css=None,
                            hook_before_toc=None)

    return complete_aug.get_result()


test_md = """

Preamble (before part starts)

# Aa  {#part:A}

beginning of part A1

# B1

lorem lorem

# B2 marked as draft {status=draft}

lorem lorem


## C1

lorem lorem


### D2

lorem lorem


## C2

lorem lorem


# A2  {#part:A2}

beginning of part A2

## A2a also a draft {status=draft}

lorem lorem

## Not draft

    """

    #     d = 'out/sec'
#     write_split_files(filename2contents, d)


@comptest
def test_formula_split():
    formula_test = """

# Section A

This is a formula: $a>b$

# Section B

This is another formula:
\[
    \sqrt{a}
\]

"""
    d = 'testf_formula_split'

    html = get_split_test_document(formula_test)
    soup = BeautifulSoup(html, 'lxml')
    html = soup.prettify().encode()
    fn = os.path.join(d, 'document_split.html')
    write_data_to_file(html, fn)

    filename2contents = split_in_files(soup)
    id2filename = get_id2filename(filename2contents)
#    add_prev_next_links(filename2contents)
#    update_refs(filename2contents, id2filename)

#    linkbase = 'link.html'
#    filename2contents[linkbase] = create_link_base(id2filename)
    for fn, s in filename2contents.items():
        write_data_to_file(str(s), os.path.join(d, 'split', fn))


#     print html
if __name__ == '__main__':
    run_module_tests()
