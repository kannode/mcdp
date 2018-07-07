# -*- coding: utf-8 -*-
import itertools
from getpass import getuser

from contracts import contract, indent
from contracts.utils import raise_desc
from mcdp import logger
from mcdp.constants import MCDPConstants
from mcdp_library import MCDPLibrary
from mcdp_report.gg_utils import embed_images_from_library2
from mcdp_utils_misc import get_md5, AugmentedResult
from mcdp_utils_xml import to_html_stripping_fragment, bs, describe_tag
from .check_missing_links import check_if_any_href_is_invalid, fix_subfig_references
from .elements_abbrevs import check_good_use_of_special_paragraphs, other_abbrevs, substitute_special_paragraphs
from .github_file_ref.display_file_imp import display_files
from .lessc import run_lessc
from .location import LocationUnknown
from .macros import replace_macros
from .make_console_pre import mark_console_pres
from .make_figures import make_figure_from_figureid_attr
from .manual_constants import MCDPManualConstants
from .prerender_math import escape_for_mathjax_back, escape_for_mathjax
from .status import check_status_codes, check_lang_codes
from .syntax_highlight import syntax_highlighting, strip_pre
from .task_markers import create_notes_from_elements
from .tocs import check_no_patently_wrong_links, fix_ids_and_add_missing
from .videos import make_videos

__all__ = [
    'render_complete',
]


@contract(returns='str', s=str, library=MCDPLibrary, raise_errors=bool)
def render_complete(library, s, raise_errors, realpath, generate_pdf=False,
                    check_refs=False, use_mathjax=True, filter_soup=None,
                    symbols=None, res=None, location=None,
                    ignore_ref_errors=False):
    """
        Transforms markdown into html and then renders the mcdp snippets inside.

        s: a markdown string with embedded html snippets

        Returns an HTML string; not a complete document.

        filter_soup(library, soup)
    """
    if res is None:
        res = AugmentedResult()
    if location is None:
        location = LocationUnknown()

    s0 = s

    unique = get_md5(realpath)[:8]
    check_good_use_of_special_paragraphs(s0, res, location)
    raise_missing_image_errors = raise_errors

    # Imports here because of circular dependencies
    from mcdp_report.gg_utils import resolve_references_to_images
    from .latex.latex_preprocess import extract_maths, extract_tabular
    from .latex.latex_preprocess import latex_preprocessing
    from .latex.latex_preprocess import replace_equations
    from .macro_col2 import col_macros, col_macros_prepare_before_markdown
    from .mark.markd import render_markdown
    from .preliminary_checks import do_preliminary_checks_and_fixes
    from .prerender_math import prerender_mathjax

    if isinstance(s, unicode):
        msg = 'I expect a str encoded with utf-8, not unicode.'
        raise_desc(TypeError, msg, s=s)

    # need to do this before do_preliminary_checks_and_fixes
    # because of & char
    s, tabulars = extract_tabular(s)

    s = do_preliminary_checks_and_fixes(s, res, location)
    # put back tabular, because extract_maths needs to grab them
    for k, v in tabulars.items():
        assert k in s
        s = s.replace(k, v)

    # copy all math content,
    #  between $$ and $$
    #  between various limiters etc.
    # returns a dict(string, substitution)
    s, maths = extract_maths(s)
    #     print('maths = %s' % maths)
    for k, v in list(maths.items()):
        if v[0] == '$' and v[1] != '$$':
            if '\n\n' in v:
                msg = 'The Markdown pre-processor got confused by this math fragment:'
                msg += '\n\n' + indent(v, '  > ')
                res.note_error(msg, location)
                maths[k] = 'ERROR'

    s = latex_preprocessing(s)
    s = '<div style="display:none">Because of mathjax bug</div>\n\n\n' + s

    # cannot parse html before markdown, because md will take
    # invalid html, (in particular '$   ciao <ciao>' and make it work)

    s = s.replace('*}', '\*}')

    s, mcdpenvs = protect_my_envs(s)
    #     print('mcdpenvs = %s' % maths)

    s = col_macros_prepare_before_markdown(s)

    #     print(indent(s, 'before markdown | '))
    s = render_markdown(s)
    #     print(indent(s, 'after  markdown | '))

    for k, v in maths.items():
        if not k in s:
            msg = 'Internal error while dealing with Latex math.'
            msg += '\nCannot find %r (= %r)' % (k, v)
            res.note_error(msg, location)
            # raise_desc(DPInternalError, msg, s=s)
            continue

        def preprocess_equations(x):
            # this gets mathjax confused
            x = x.replace('>', '\\gt{}')  # need brace; think a<b -> a\lt{}b
            x = x.replace('<', '\\lt{}')
            #             print('replaced equation %r by %r ' % (x0, x))
            return x

        v = preprocess_equations(v)
        s = s.replace(k, v)

    s = replace_equations(s)
    s = s.replace('\\*}', '*}')

    # this parses the XML
    soup = bs(s)

    other_abbrevs(soup, res, location)

    substitute_special_paragraphs(soup, res, location)
    create_notes_from_elements(soup, res, location, unique)

    # need to process tabular before mathjax
    escape_for_mathjax(soup)

    #     print(indent(s, 'before prerender_mathjax | '))
    # mathjax must be after markdown because of code blocks using "$"

    s = to_html_stripping_fragment(soup)

    if use_mathjax:
        s = prerender_mathjax(s, symbols, res)

    soup = bs(s)
    escape_for_mathjax_back(soup)
    s = to_html_stripping_fragment(soup)

    #     print(indent(s, 'after prerender_mathjax | '))
    for k, v in mcdpenvs.items():
        # there is this case:
        # ~~~
        # <pre> </pre>
        # ~~~
        s = s.replace(k, v)

    s = s.replace('<p>DRAFT</p>', '<div class="draft">')

    s = s.replace('<p>/DRAFT</p>', '</div>')

    soup = bs(s)
    mark_console_pres(soup, res, location)

    # try:

    # except Exception as e:
    #     msg = 'I got an error while substituting github: references.'
    #     msg += '\nI will ignore this error because it might not be the fault of the writer.'
    #     msg += '\n\n' + indent(str(e), '|', ' error: |')
    #

    # must be before make_figure_from_figureid_attr()
    display_files(soup, defaults={}, res=res, location=location, raise_errors=raise_errors)

    make_figure_from_figureid_attr(soup, res, location)
    col_macros(soup)
    fix_subfig_references(soup)

    library = get_library_from_document(soup, default_library=library)

    from .highlight import html_interpret
    html_interpret(library, soup, generate_pdf=generate_pdf,
                   raise_errors=raise_errors, realpath=realpath, res=res, location=location)
    if filter_soup is not None:
        filter_soup(library=library, soup=soup)

    if False:
        embed_images_from_library2(soup=soup, library=library,
                                   raise_errors=raise_missing_image_errors,
                                   res=res, location=location)
    else:
        resolve_references_to_images(soup=soup, library=library,
                                     raise_errors=raise_missing_image_errors,
                                     res=res, location=location)

    make_videos(soup, res, location, raise_on_errors=False)

    if check_refs:
        check_if_any_href_is_invalid(soup, res, location, ignore_ref_errors=ignore_ref_errors)

    if False:
        if getuser() == 'andrea':
            if MCDPConstants.preprocess_style_using_less:
                run_lessc(soup)
            else:
                logger.warning(
                        'preprocess_style_using_less=False might break the manual')

    fix_validation_problems(soup)

    strip_pre(soup)

    if MCDPManualConstants.enable_syntax_higlighting:
        syntax_highlighting(soup)

    if MCDPManualConstants.enforce_lang_attribute:
        check_lang_codes(soup, res, location)

    # Fixes the IDs (adding 'sec:'); add IDs to missing ones
    globally_unique_id_part = 'autoid-DO-NOT-USE-THIS-VERY-UNSTABLE-LINK-' + get_md5(realpath)[:8]
    fix_ids_and_add_missing(soup, globally_unique_id_part, res, location)

    check_no_patently_wrong_links(soup, res, location)

    if MCDPManualConstants.enforce_status_attribute:
        check_status_codes(soup, realpath, res, location)

    s = to_html_stripping_fragment(soup)
    s = replace_macros(s)

    return s


def get_document_properties(soup):
    """ Reads a document's <meta> tags into a dict """
    metas = list(soup.select('meta'))
    FK, FV = 'name', 'content'
    properties = {}
    for e in metas:
        if not FK in e.attrs or not FV in e.attrs:
            msg = 'Expected "%s" and "%s" attribute for meta tag.' % (FK, FV)
            raise_desc(ValueError, msg, tag=describe_tag(e))

        properties[e[FK]] = e[FV]
    return properties


def get_library_from_document(soup, default_library):
    """
        Reads a tag like this:

            <meta name="mcdp-library" content='am'/>

    """
    properties = get_document_properties(soup)

    KEY_MCDP_LIBRARY = 'mcdp-library'
    if KEY_MCDP_LIBRARY in properties:
        use = properties[KEY_MCDP_LIBRARY]
        # print('using library %r ' % use)
        library = default_library.load_library(use)
        return library

    return default_library


def fix_validation_problems(soup):
    """ Fixes things that make the document not validate. """

    # remove the attributes span.c and span.ce used in ast_to_html
    for e in soup.select('span[c]'):
        del e.attrs['c']
    for e in soup.select('span[ce]'):
        del e.attrs['ce']

    also_remove = ['figure-id', 'figure-class', 'figure-caption']
    also_remove.extend('make-col%d' % _ for _ in range(1, 12))

    for a in also_remove:
        for e in soup.select('[%s]' % a):
            del e.attrs[a]

    # add missing type for <style>
    for e in soup.select('style'):
        if not 'type' in e.attrs:
            e.attrs['type'] = 'text/css'

    # if False:
    #     for e in soup.select('span.MathJax_SVG'):
    #         style = e.attrs['style']
    #         style = style.replace('display: inline-block;',
    #                               '/* decided-to-ignore-inline-block: 0;*/')
    #         e.attrs['style'] = style


def protect_my_envs(s):
    from mcdp_docs.mark.markdown_transform import is_inside_markdown_quoted_block

    # we don't want MathJax to look inside these
    elements = ['mcdp-value', 'mcdp-poset', 'pre', 'render',
                'poset', 'pos',
                'value', 'val']
    # "poset" must be before "pos"
    # "value" must be before "val"

    for e1, e2 in itertools.product(elements, elements):
        if e1 == e2:
            continue
        if e1.startswith(e2):
            assert elements.index(e1) < elements.index(e2)

    delimiters = []
    for e in elements:
        delimiters.append(('<%s' % e, '</%s>' % e))

    subs = {}
    for d1, d2 in delimiters:
        from .latex.latex_preprocess import extract_delimited
        s = extract_delimited(s, d1, d2, subs, 'MYENVS')

    for k, v in list(subs.items()):
        # replace back if k is in a line that is a comment
        # or there is an odd numbers of \n~~~
        if k in s:  # it might be recursively inside something
            if is_inside_markdown_quoted_block(s, s.index(k)):
                s = s.replace(k, v)
                del subs[k]

    return s, subs
