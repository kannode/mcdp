#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys
from collections import OrderedDict, namedtuple
from contextlib import contextmanager

from bs4 import BeautifulSoup
from bs4.element import Comment, Tag, NavigableString
from contracts import contract
from contracts.utils import raise_desc, indent, check_isinstance
from mcdp.logs import logger
from mcdp_docs.add_edit_links import add_github_links_if_edit_url
from mcdp_docs.check_missing_links import detect_duplicate_IDs, get_id2element
from mcdp_docs.github_file_ref.substitute_github_refs_i import substitute_github_refs
from mcdp_docs.location import LocationUnknown, HTMLIDLocation
from mcdp_docs.manual_constants import MCDPManualConstants
from mcdp_utils_misc import AugmentedResult
from mcdp_utils_misc.timing import timeit_wall as timeit
from mcdp_utils_xml import add_class, bs, copy_contents_into

from .footnote_javascript import add_footnote_polyfill
from .macros import replace_macros
from .minimal_doc import add_extra_css
from .moving_copying_deleting import move_things_around
from .read_bibtex import extract_bibtex_blocks
from .tocs import generate_toc, substituting_empty_links, LABEL_WHAT_NUMBER, LABEL_WHAT_NUMBER_NAME, LABEL_WHAT, \
    LABEL_NUMBER, LABEL_NAME, LABEL_SELF


def get_manual_css_frag():
    """ Returns fragment of doc with CSS, either inline or linked,
        depending on MCDPConstants.manual_link_css_instead_of_including. """
    from mcdp import MCDPConstants

    link_css = MCDPConstants.manual_link_css_instead_of_including

    frag = Tag(name='fragment-css')
    if link_css:

        link = Tag(name='link')
        link['rel'] = 'stylesheet'
        link['type'] = 'text/css'
        link['href'] = 'VERSIONCSS'

        return frag
    else:
        assert False


DocToJoin = namedtuple('DocToJoin', 'docname contents source_info')


@contract(files_contents='list', returns='str',
          remove_selectors='None|seq(str)')
def manual_join(template, files_contents,
                stylesheet, remove=None, extra_css=None,
                remove_selectors=None,
                hook_before_toc=None,
                references=None,
                resolve_references=True,
                hook_before_final_pass=None,
                require_toc_placeholder=False,
                permalink_prefix=None,
                crossrefs_aug=None,
                aug0=None):
    """
        files_contents: a list of tuples that can be cast to DocToJoin:
        where the string is a unique one to be used for job naming.

        extra_css: if not None, a string of more CSS to be added
        Remove_selectors: list of selectors to remove (e.g. ".draft").

        hook_before_toc if not None is called with hook_before_toc(soup=soup)
        just before generating the toc
    """
    result = AugmentedResult()

    if references is None:
        references = {}
    check_isinstance(files_contents, list)

    if crossrefs_aug is None:
        crossrefs = Tag(name='no-cross-refs')
    else:
        crossrefs = bs(crossrefs_aug.get_result())
        result.merge(crossrefs_aug)
    if aug0 is not None:
        result.merge(aug0)

    @contextmanager
    def timeit(_):
        yield

    with timeit('manual_join'):

        files_contents = [DocToJoin(*_) for _ in files_contents]

        # cannot use bs because entire document
        with timeit('parsing template'):
            template0 = template
            template = replace_macros(template)
            template_soup = BeautifulSoup(template, 'lxml', from_encoding='utf-8')
            d = template_soup
            if d.html is None:
                s = "Invalid template"
                raise_desc(ValueError, s, template0=template0)

        with timeit('adding head'):
            assert d.html is not None
            assert '<html' in str(d)
            head = d.find('head')
            if head is None:
                msg = 'Could not find <head> in template:'
                logger.error(msg)
                logger.error(str(d))
                raise Exception(msg)
            assert head is not None
            for x in get_manual_css_frag().contents:
                head.append(x.__copy__())

        with timeit('adding stylesheet'):
            if stylesheet is not None:
                link = Tag(name='link')
                link['rel'] = 'stylesheet'
                link['type'] = 'text/css'
                from mcdp_report.html import get_css_filename
                link['href'] = get_css_filename('compiled/%s' % stylesheet)
                head.append(link)

        with timeit('making basename2soup'):
            basename2soup = OrderedDict()
            for doc_to_join in files_contents:
                if doc_to_join.docname in basename2soup:
                    msg = 'Repeated docname %r' % doc_to_join.docname
                    raise ValueError(msg)
                from .latex.latex_preprocess import assert_not_inside
                if isinstance(doc_to_join.contents, AugmentedResult):
                    result.merge(doc_to_join.contents)
                    contents = doc_to_join.contents.get_result()
                else:
                    contents = doc_to_join.contents
                assert_not_inside(contents, '<fragment')
                assert_not_inside(contents, 'DOCTYPE')

                frag = bs(contents)
                basename2soup[doc_to_join.docname] = frag

        # with timeit('fix_duplicate_ids'):
        # XXX
        # fix_duplicated_ids(basename2soup)

        with timeit('copy contents'):
            body = d.find('body')
            add_comments = False

            for docname, content in basename2soup.items():
                if add_comments:
                    body.append(NavigableString('\n\n'))
                    body.append(Comment('Beginning of document dump of %r' % docname))
                    body.append(NavigableString('\n\n'))

                try_faster = True
                if try_faster:
                    for e in list(content.children):
                        body.append(e.extract())
                else:
                    copy_contents_into(content, body)

                if add_comments:
                    body.append(NavigableString('\n\n'))
                    body.append(Comment('End of document dump of %r' % docname))
                    body.append(NavigableString('\n\n'))

        with timeit('extract_bibtex_blocks'):
            extract_bibtex_blocks(d)

        with timeit('ID_PUT_BIB_HERE'):

            ID_PUT_BIB_HERE = MCDPManualConstants.ID_PUT_BIB_HERE

            bibhere = d.find('div', id=ID_PUT_BIB_HERE)
            if bibhere is None:
                msg = ('Could not find #%s in document. '
                       'Adding one at end of document.') % ID_PUT_BIB_HERE
                result.note_warning(msg)
                bibhere = Tag(name='div')
                bibhere.attrs['id'] = ID_PUT_BIB_HERE
                d.find('body').append(bibhere)

            do_bib(d, bibhere)

        with timeit('hook_before_final_pass'):
            if hook_before_final_pass is not None:
                hook_before_final_pass(soup=d)

        with timeit('document_final_pass_before_toc'):
            document_final_pass_before_toc(d, remove, remove_selectors, result)

        with timeit('hook_before_toc'):
            if hook_before_toc is not None:
                hook_before_toc(soup=d)

        with timeit('generate_and_add_toc'):
            try:
                generate_and_add_toc(d, raise_error=True, aug=result)
            except NoTocPlaceholder as e:
                if require_toc_placeholder:
                    msg = 'Could not find toc placeholder: %s' % e
                    # logger.error(msg)
                    if aug0 is not None:
                        result.note_error(msg)
                    else:
                        raise Exception(msg)

        with timeit('document_final_pass_after_toc'):
            document_final_pass_after_toc(soup=d, crossrefs=crossrefs,
                                          resolve_references=resolve_references, res=result)

        if extra_css is not None:
            logger.info('adding extra CSS')
            add_extra_css(d, extra_css)

        with timeit('document_only_once'):
            document_only_once(d)

        location = LocationUnknown()
        substitute_github_refs(d, defaults={}, res=result, location=location)

        with timeit('another A pass'):
            for a in d.select('a[href]'):
                href = a.attrs['href']
                if href in references:
                    r = references[href]
                    a.attrs['href'] = r.url
                    if not a.children:  # empty
                        a.append(r.title)

        # do not use to_html_stripping_fragment - this is a complete doc
        # mark_in_html(result, soup=d)

        add_github_links_if_edit_url(soup=d, permalink_prefix=permalink_prefix)

        with timeit('converting to string'):
            res = unicode(d)

        with timeit('encoding'):
            res = res.encode('utf8')

        logger.info('done - %.1f MB' % (len(res) / (1024 * 1024.0)))

        result.set_result(res)
        return result


def find_first_parent_section(e):
    parent = e.parent

    def good(x):
        return x.name == 'section' and 'with-header-inside' in x.attrs['class']

    while not good(parent):
        parent = parent.parent
        if parent is None:
            raise ValueError()
    return parent


def split_robustly(what, sep):
    if not what:
        return []
    return [x.strip() for x in what.split(sep) if x.strip()]


ATTR_ASSIGNMENT = 'assignment'


def process_assignment(soup, res):
    sep = ','
    for e in soup.select('.assignment'):
        parent = find_first_parent_section(e)
        current = split_robustly(parent.attrs.get(ATTR_ASSIGNMENT, ''), sep)
        more = split_robustly(e.string, sep)
        now = current + more
        parent.attrs[ATTR_ASSIGNMENT] = sep.join(now)
    fix_notes_assignees(soup, res)


def fix_notes_assignees(soup, res):
    id2element, duplicates = get_id2element(soup, 'id')

    assert isinstance(res, AugmentedResult)
    # logger.warn('here: %s' % len(res.notes))
    for note in res.notes:
        locations = note.locations
        if len(locations) == 1:
            location = list(locations.values())[0]
            if isinstance(location, HTMLIDLocation):
                ID = location.element_id
                if ID in id2element:
                    element = id2element[ID]
                    assignees = get_assignees_from_parents(element)
                    if assignees:
                        tags = list(note.tags)
                        for a in assignees:
                            tags.append('for:%s' % a)
                        note.tags = tuple(sorted(set(tags)))
                    else:
                        pass
                        # logger.warn('could not find assignees for %s' % ID)
                else:
                    pass
                    logger.warn('could not find element %r' % ID)


def get_assignees_from_parents(element):
    parent = element.parent
    while True:
        # print('considering %s %s' % (parent.name, parent.attrs))
        if ATTR_ASSIGNMENT in parent.attrs:
            found = split_robustly(parent.attrs[ATTR_ASSIGNMENT], ',')
            # logger.info('found assignment %s' % found)
            return found
        parent = parent.parent
        if parent is None:
            # logger.warn('Could not find any assignment')
            return []


def document_final_pass_before_toc(soup, remove, remove_selectors, res=None):
    if res is None:
        logger.warn('no res passed')

    logger.info('reorganizing contents in <sections>')

    with timeit('find body'):
        body = soup.find('body')
        if body is None:
            msg = 'Cannot find <body>:\n%s' % indent(str(soup)[:1000], '|')
            raise ValueError(msg)

    with timeit('reorganize_contents'):
        body2 = reorganize_contents(body)

    process_assignment(body2, res)

    body.replace_with(body2)

    # Removing stuff
    with timeit('remove stuff'):
        do_remove_stuff(body2, remove_selectors, remove)

    with timeit('move_things_around'):
        move_things_around(soup=soup, res=res)


def document_final_pass_after_toc(soup, crossrefs=None, resolve_references=True, res=None, location=LocationUnknown()):
    if res is None:
        res = AugmentedResult()
    """ This is done to a final document """

    logger.info('checking errors')
    check_various_errors(soup)

    from .check_missing_links import check_if_any_href_is_invalid
    logger.info('checking hrefs')
    check_if_any_href_is_invalid(soup, res, location, extra_refs=crossrefs)

    # Note that this should be done *after* check_if_any_href_is_invalid()
    # because that one might fix some references
    if resolve_references:
        logger.info('substituting empty links')

        substituting_empty_links(soup, raise_errors=False, res=res, extra_refs=crossrefs)

    for a in soup.select('a[href_external]'):
        a.attrs['href'] = a.attrs['href_external']
        add_class(a, 'interdoc')

    detect_duplicate_IDs(soup, res)

    # warn_for_duplicated_ids(soup)


def document_only_once(html_soup):
    add_footnote_polyfill(html_soup)


def do_bib(soup, bibhere):
    """ find used bibliography entries put them there """
    used = []
    unused = set()
    for a in soup.find_all('a'):
        href = a.attrs.get('href', '')
        if href.startswith('#bib:'):
            used.append(href[1:])  # no "#"
    logger.debug('I found %d references, to these: %s' % (len(used), used))

    # collect all the <cite>
    id2cite = {}
    for c in soup.find_all('cite'):
        ID = c.attrs.get('id', None)
        id2cite[ID] = c
        if ID in used:
            add_class(c, 'used')
        else:
            unused.add(ID)
            add_class(c, 'unused')

    # divide in found and not found
    found = []
    notfound = []
    for ID in used:
        if not ID in id2cite:
            if not ID in notfound:
                notfound.append(ID)
        else:
            found.append(ID)

    # now create additional <cite> for the ones that are not found
    for ID in notfound:
        cite = Tag(name='cite')
        s = 'Reference %s not found.' % ID
        cite.append(NavigableString(s))
        cite.attrs['class'] = ['errored', 'error']  # XXX
        soup.append(cite)
        id2cite[ID] = cite

    # now number the cites
    n = 1
    id2number = {}
    for ID in used:
        if not ID in id2number:
            id2number[ID] = n
        n += 1

    # now add the attributes for cross-referencing
    for ID in used:
        number = id2number[ID]
        cite = id2cite[ID]

        cite.attrs[LABEL_NAME] = '[%s]' % number
        cite.attrs[LABEL_SELF] = '[%s]' % number
        cite.attrs[LABEL_NUMBER] = number
        cite.attrs[LABEL_WHAT] = 'Reference'
        cite.attrs[LABEL_WHAT_NUMBER_NAME] = '[%s]' % number
        cite.attrs[LABEL_WHAT_NUMBER] = '[%s]' % number

    # now put the cites at the end of the document
    for ID in used:
        c = id2cite[ID]
        # remove it from parent
        c.extract()
        #         logger.debug('Extracting cite for %r: %s' % (ID, c))
        # add to bibliography
        bibhere.append(c)

    s = ("Bib cites: %d\nBib used: %s\nfound: %s\nnot found: %s\nunused: %d"
         % (len(id2cite), len(used), len(found), len(notfound), len(unused)))
    logger.info(s)


def can_ignore_duplicated_id(element):
    id_ = element.attrs['id']
    for x in ['node', 'clust', 'edge', 'graph', 'MathJax', 'mjx-eqn']:
        if id_.startswith(x):
            return True

    for _ in element.parents:
        if _.name == 'svg':
            return True

    # print('need %s' % id_)
    return False


def warn_for_duplicated_ids(soup):
    from collections import defaultdict

    counts = defaultdict(lambda: [])
    for e in soup.select('[id]'):
        ID = e['id']
        counts[ID].append(e)

    problematic = []
    for ID, elements in counts.items():
        n = len(elements)
        if n == 1:
            continue
        for e in elements:
            if can_ignore_duplicated_id(e):
                continue

        # msg = ('ID %15s: found %s - numbering will be screwed up' % (ID, n))
        # logger.error(msg)
        problematic.append(ID)

        for e in elements:
            t = Tag(name='span')
            t['class'] = 'duplicated-id'
            t.string = 'Error: warn_for_duplicated_ids:  There are %d tags with ID %s' % (
                n, ID)
            # e.insert_before(t)
            add_class(e, 'errored')

        for i, e in enumerate(elements[1:]):
            e['id'] = e['id'] + '-duplicate-%d' % (i + 1)
            # print('changing ID to %r' % e['id'])
    if problematic:
        logger.error('The following IDs were duplicated: %s' %
                     ", ".join(problematic))
        logger.error(
                'I renamed some of them; references and numbering are screwed up')


def fix_duplicated_ids(basename2soup):
    """
        fragments is a list of soups that might have
        duplicated ids.
    """
    id2frag = {}
    tochange = []  # (i, from, to)
    for basename, fragment in basename2soup.items():
        # get all the ids for fragment
        for element in fragment.find_all(id=True):
            id_ = element.attrs['id']
            # ignore the mathjax stuff
            if 'MathJax' in id_:  # or id_.startswith('MJ'):
                continue
            if id_.startswith('node') or id_.startswith('edge'):
                continue
            # is this a new ID
            if not id_ in id2frag:
                id2frag[id_] = basename
            else:  # already know it
                if id2frag[id_] == basename:
                    # frome the same frag
                    logger.debug(
                            'duplicated id %r inside frag %s' % (id_, basename))
                else:
                    # from another frag
                    # we need to rename all references in this fragment
                    # '%s' % random.randint(0,1000000)
                    new_id = id_ + '-' + basename
                    element['id'] = new_id
                    tochange.append((basename, id_, new_id))
    # logger.info(tochange)
    for i, id_, new_id in tochange:
        fragment = basename2soup[i]
        for a in fragment.find_all(href="#" + id_):
            a.attrs['href'] = '#' + new_id


def reorganize_contents(body0, add_debug_comments=False):
    """ reorganizes contents

        h1
        h2
        h1

        section
            h1
            h2
        section
            h1

    """
    # if False:
    # write_data_to_file(str(body0), 'before-reorg.html')

    with timeit('reorganize_by_parts'):
        reorganized = reorganize_by_books(body0)
        # reorganized = reorganize_by_parts(body0)

    with timeit('dissolving'):
        # now dissolve all the elements of the type <div class='without-header-inside'>
        options = ['without-header-inside', 'with-header-inside']
        for x in reorganized.find_all('div', attrs=
        {'class':
             lambda _: _ is not None and _ in options}):
            dissolve(x)

    return reorganized


def dissolve(x):
    index = x.parent.index(x)
    for child in list(x.contents):
        child.extract()
        x.parent.insert(index, child)
        index += 1

    x.extract()


ATTR_PREV = 'prev'
ATTR_NEXT = 'next'
CLASS_LINK_NEXT = 'link_next'
CLASS_LINK_PREV = 'link_prev'


def add_prev_next_links(filename2contents, only_for=None):
    new_one = OrderedDict()
    for filename, contents in list(filename2contents.items()):
        if only_for and not filename in only_for: continue

        id_prev = contents.attrs[ATTR_PREV]
        a_prev = Tag(name='a')
        a_prev.attrs['href'] = '#' + str(id_prev)
        a_prev.attrs['class'] = CLASS_LINK_PREV
        a_prev.append('prev')

        id_next = contents.attrs[ATTR_NEXT]
        a_next = Tag(name='a')
        a_next.attrs['href'] = '#' + str(id_next)
        a_next.attrs['class'] = CLASS_LINK_NEXT
        a_next.append('next')

        S = Tag(name='div')
        S.attrs['class'] = ['super']

        nav1 = Tag(name='div')
        add_class(nav1, 'navigation')
        if id_prev:
            nav1.append(a_prev.__copy__())
        if id_next:
            nav1.append(a_next.__copy__())
        spacer = Tag(name='div')
        spacer.attrs['style'] = 'clear:both'
        nav1.append(spacer)

        add_class(contents, 'main-section-for-page')

        contents2 = contents
        S.append(contents2)

        from .source_info_imp import get_main_header
        actual_id = get_main_header(contents2)

        if False:  # just checking
            e = contents2.find(id=actual_id)
            if e is not None:
                pass
            else:
                logger.error('not found %r' % actual_id)
        S.attrs['id'] = actual_id

        contents2.insert(0, nav1.__copy__())
        contents2.append(nav1.__copy__())

        new_one[filename] = S

    return new_one


def split_in_files(body, levels=['sec', 'part', 'book']):
    """
        Returns an ordered dictionary filename -> contents
    """
    file2contents = OrderedDict()

    # now find all the sections in order
    sections = []

    for section in body.select('section.with-header-inside'):
        level = section.attrs[ATTR_LEVEL]
        if level in levels:
            # section.extract()
            sections.append(section)

    for i, section in enumerate(sections):
        if 'id' not in section.attrs:
            section.attrs['id'] = 'page%d' % i

    filenames = []
    for i, section in enumerate(sections):
        if i < len(sections) - 1:
            section.attrs[ATTR_NEXT] = sections[i + 1].attrs['id']
        else:
            section.attrs[ATTR_NEXT] = ""
        if i == 0:
            section.attrs[ATTR_PREV] = ""
        else:
            section.attrs[ATTR_PREV] = sections[i - 1].attrs['id']

        id_ = section.attrs['id']
        id_sanitized = id_.replace(':', '_').replace('-', '_').replace('_section', '').replace('/', '_')

        #         filename = '%03d_%s.html' % (i, id_sanitized)
        filename = '%s.html' % id_sanitized

        if filename in filenames:
            for ii in range(1000):
                filename = '%s-%d.html' % (id_sanitized, ii)
                if filename not in filenames:
                    break

        assert filename not in filenames
        filenames.append(filename)

    f0 = OrderedDict()
    for filename, section in reversed(zip(filenames, sections)):
        section.extract()
        assert not filename in f0
        f0[filename] = section

    for k, v in reversed(f0.items()):
        file2contents[k] = v
    #
    for filename, section in file2contents.items():
        if len(list(section.descendants)) < 2:
            del file2contents[filename]

    # rename the first to be called index.html
    name_for_first = 'index.html'
    first = list(file2contents)[0]

    # add remaining material of body in first section
    body.name = 'div'
    body.attrs['class'] = 'remaining-material'
    body.extract()
    file2contents[first].insert(0, body)

    file2contents = OrderedDict([(name_for_first if k == first else k, v)
                                 for k, v in file2contents.items()])

    ids = []
    for i, (filename, section) in enumerate(file2contents.items()):
        ids.append(section.attrs['id'])

    for i, (filename, section) in enumerate(file2contents.items()):
        if i < len(ids) - 1:
            section.attrs[ATTR_NEXT] = ids[i + 1]
        else:
            section.attrs[ATTR_NEXT] = ""
        if i == 0:
            section.attrs[ATTR_PREV] = ""
        else:
            section.attrs[ATTR_PREV] = ids[i - 1]

    return file2contents


def get_id2filename(filename2contents):
    ignore_these = [
        'tocdiv', 'not-toc', 'disqus_thread',
        'disqus_section', 'dsq-count-scr', 'banner',
        'MathJax_SVG_glyphs', 'MathJax_SVG_styles',
    ]

    id2filename = {}

    for filename, contents in filename2contents.items():

        for element in contents.select('[id]'):
            if can_ignore_duplicated_id(element):
                continue

            id_ = element.attrs['id']

            if id_ in ignore_these:
                continue

            if id_ in id2filename:
                logger.error('double element with ID %s' % id_)
            #                    logger.error(str(element.parent()))

            id2filename[id_] = filename

        # also don't forget the id for the entire section
        if 'id' in contents.attrs:
            id_ = contents.attrs['id']
            id2filename[id_] = filename

    return id2filename


def update_refs(filename2contents, id2filename):
    for filename, contents in filename2contents.items():
        update_refs_(filename, contents, id2filename)


def update_refs_(filename, contents, id2filename):
    test_href = lambda _: _ is not None and _.startswith('#')
    elements = list(contents.find_all('a', attrs={'href': test_href}))
    # logger.debug('updates: %s' % sorted(id2filename))
    for a in elements:
        href = a.attrs['href']
        assert href[0] == '#'
        id_ = href[1:]
        if id_ in id2filename:
            point_to_filename = id2filename[id_]
            if point_to_filename != filename:
                new_href = '%s#%s' % (point_to_filename, id_)
                a.attrs['href'] = new_href
                add_class(a, 'link-different-file')
            else:
                # actually it doesn't change
                new_href = '#%s' % id_
                a.attrs['href'] = new_href
                add_class(a, 'link-same-file')

                if 'toc_link' in a.attrs['class']:
                    p = a.parent
                    assert p.name == 'li'
                    add_class(p, 'link-same-file-direct-parent')

                    # now find all the lis
                    for x in list(p.descendants):
                        if isinstance(x, Tag) and x.name == 'li':
                            add_class(x, 'link-same-file-inside')

                p = a.parent
                while p:
                    if isinstance(p, Tag) and p.name in ['ul', 'li']:
                        add_class(p, 'contains-link-same-file')
                    p = p.parent
        else:
            logger.error('update_ref() for %r: no element with ID "%s".' % (filename, id_))


def tag_like(t):
    t2 = Tag(name=t.name)
    for k, v in t.attrs.items():
        t2.attrs[k] = v
    return t2


def is_chapter_marker(x):
    return isinstance(x, Tag) and \
           x.name == 'h1' and \
           (not 'part:' in x.attrs.get('id', '')) and \
           (not 'book:' in x.attrs.get('id', ''))


def is_part_marker(x):
    if not isinstance(x, Tag):
        return False
    if not x.name == 'h1':
        return False

    id_ = x.attrs.get('id', '')
    id_starts_with_part = id_.startswith('part:')
    return id_starts_with_part


def is_book_marker(x):
    if not isinstance(x, Tag):
        return False
    if not x.name == 'h1':
        return False

    id_ = x.attrs.get('id', '')
    id_starts_with_part = id_.startswith('book:')
    return id_starts_with_part


ATTR_LEVEL = 'level'

CLASS_WITH_HEADER = 'with-header-inside'
CLASS_WITHOUT_HEADER = 'without-header-inside'


def reorganize_by_books(body):
    elements = list(body.contents)
    with timeit('reorganize_by_book:make_sections'):
        sections = make_sections2(elements, is_book_marker, attrs={'level': 'book-down'})

    with timeit('reorganize_by_book:copying'):
        res = tag_like(body)

        for header, section in sections:
            if not header:
                S = Tag(name='section')
                S.attrs[ATTR_LEVEL] = 'book'
                S.attrs['class'] = CLASS_WITHOUT_HEADER
                section2 = reorganize_by_parts(section)
                S.append(section2)
                res.append(S)
            else:
                S = Tag(name='section')
                S.attrs[ATTR_LEVEL] = 'book'
                S.attrs['class'] = CLASS_WITH_HEADER
                S.append(header)
                section2 = reorganize_by_parts(section)
                S.append(section2)
                copy_attributes_from_header(S, header)
                res.append(S)
        return res


def reorganize_by_parts(body):
    elements = list(body.contents)
    with timeit('reorganize_by_parts:make_sections'):
        sections = make_sections2(elements, is_part_marker, attrs={'level': 'part-down'})

    with timeit('reorganize_by_parts:copying'):
        res = tag_like(body)

        for header, section in sections:
            if not header:
                S = Tag(name='section')
                S.attrs[ATTR_LEVEL] = 'part'
                S.attrs['class'] = CLASS_WITHOUT_HEADER
                section2 = reorganize_by_chapters(section)
                S.append(section2)
                res.append(S)
            else:
                S = Tag(name='section')
                S.attrs[ATTR_LEVEL] = 'part'
                S.attrs['class'] = CLASS_WITH_HEADER
                S.append(header)
                section2 = reorganize_by_chapters(section)
                S.append(section2)
                copy_attributes_from_header(S, header)
                res.append(S)
        return res


def reorganize_by_chapters(section):
    elements = list(section.contents)
    sections = make_sections2(elements, is_chapter_marker, attrs={'level': 'sec-down'})
    res = tag_like(section)
    for header, section in sections:
        if not header:

            S = Tag(name='section')
            S.attrs[ATTR_LEVEL] = 'sec'
            S.attrs['class'] = CLASS_WITHOUT_HEADER
            section2 = reorganize_by_section(section)
            S.append(section2)
            res.append(S)

        else:
            S = Tag(name='section')
            S.attrs[ATTR_LEVEL] = 'sec'
            S.attrs['class'] = CLASS_WITH_HEADER
            S.append(header)
            section2 = reorganize_by_section(section)
            S.append(section2)
            copy_attributes_from_header(S, header)
            res.append(S)
    return res


def reorganize_by_section(section):
    def is_section_marker(x):
        return isinstance(x, Tag) and x.name == 'h2'

    elements = list(section.contents)
    sections = make_sections2(elements, is_section_marker, attrs={'level': 'sub-down'})
    res = tag_like(section)
    for header, section in sections:
        if not header:
            S = Tag(name='section')
            S.attrs[ATTR_LEVEL] = 'sub'
            S.attrs['class'] = CLASS_WITHOUT_HEADER
            S.append(section)
            res.append(S)
        else:
            S = Tag(name='section')
            S.attrs[ATTR_LEVEL] = 'sub'
            S.attrs['class'] = CLASS_WITH_HEADER
            S.append(header)
            section2 = reorganize_by_subsection(section)
            S.append(section2)
            copy_attributes_from_header(S, header)
            res.append(S)

    return res


def reorganize_by_subsection(section):
    def is_section_marker(x):
        return isinstance(x, Tag) and x.name == 'h3'

    elements = list(section.contents)
    sections = make_sections2(elements, is_section_marker, attrs={'level': 'subsub-down'})
    res = tag_like(section)
    for header, section in sections:
        if not header:
            S = Tag(name='section')
            S.attrs[ATTR_LEVEL] = 'subsub'
            S.attrs['class'] = CLASS_WITHOUT_HEADER
            S.append(section)
            res.append(S)
        else:
            S = Tag(name='section')
            S.attrs[ATTR_LEVEL] = 'subsub'
            S.attrs['class'] = CLASS_WITH_HEADER
            S.append(header)
            S.append(section)
            copy_attributes_from_header(S, header)
            res.append(S)

    return res


def copy_attributes_from_header(section, header):
    """
        Note that for section, if header is "sec:Blah",
        we give the id "blah:section", so it's easier to link to it.
    """
    assert section.name == 'section'
    if not 'id' in header.attrs:
        msg = 'This header has no ID'
        msg += '\n' + str(header)
        raise Exception(msg)

    from mcdp_docs.composing.cli import remove_prefix
    pure_id = remove_prefix(header.attrs['id'])

    section.attrs['id'] = pure_id + ':section'
    for c in header.attrs.get('class', []):
        add_class(section, c)

    for a in MCDPManualConstants.attrs_to_copy_from_header_to_section:
        if a in header.attrs:
            section.attrs[a] = header.attrs[a]


def make_sections2(elements, is_marker, copy=False, element_name='div', attrs={},
                   add_debug_comments=False):
    def debug(s):
        if False:
            logger.debug(s)

    sections = []

    def make_new():
        tx = Tag(name=element_name)
        for k, v in attrs.items():
            tx.attrs[k] = v
        return tx

    current_header = None
    current_section = make_new()

    current_section['class'] = 'without-header-inside'

    for x in elements:
        if is_marker(x):
            if contains_something_else_than_space(current_section):
                sections.append((current_header, current_section))

            current_section = make_new()
            debug('marker %s' % x.attrs.get('id', 'unnamed'))
            current_header = x.__copy__()
            current_section['class'] = 'with-header-inside'
        else:
            x2 = x.__copy__() if copy else x.extract()
            current_section.append(x2)

    if current_header or contains_something_else_than_space(current_section):
        sections.append((current_header, current_section))

    debug('make_sections: %s found using marker %s' %
          (len(sections), is_marker.__name__))
    return sections


def contains_something_else_than_space(element):
    for c in element.contents:
        if not isinstance(c, NavigableString):
            return True
        if c.string.strip():
            return True
    return False


def check_various_errors(d):
    error_names = ['DPSemanticError', 'DPSyntaxError']
    selector = ", ".join('.' + _ for _ in error_names)
    errors = list(d.find_all(selector))
    if errors:
        msg = 'I found %d errors in processing.' % len(errors)
        logger.error(msg)
        for e in errors:
            logger.error(e.contents)

    fragments = list(d.find_all('fragment'))
    if fragments:
        msg = 'There are %d spurious elements "fragment".' % len(fragments)
        logger.error(msg)


def debug(s):
    sys.stderr.write(str(s) + ' \n')


# language=javascript
jump_script = """
id2fragment = {};

for(fragment in links) {
    // remove ":section"
    // remove XXX:
    i = fragment.indexOf(':');
    if(i>0) {
        rest = fragment.substring(i+1);
        id2fragment[rest] = fragment;
    } else {
       id2fragment[fragment] = fragment;
    }
}

function log(s) {
    console.info(s);
    var p = document.createElement('p');
    p.innerHTML = s;

    // var body = document.getElementsByTagName('body');
    document.body.appendChild(p);
}

if(window.location.hash) {
    hash = window.location.hash;
    hashid = hash.substring(1);
    console.info(hashid);
    if (hashid in id2fragment) {
        fragment = id2fragment[hashid];
        filename = links[fragment];
        outlink = filename + '#' + fragment;
        log("Redirecting to <a href='"+outlink+"'><code>" + outlink+ "</code></a>");
        window.location = outlink;
    } else {
        log("Could not find reference <code>" + hashid+ "</code>.");
        log("This means that the text to which it refers has not made it to the master branch yet.");
        log("Or, it might mean that the bot has not compiled and published the new book version yet.");
        log("Note that this is completely normal if you are creating a new section.");
    }
} else {
    log("No hash found");
}
"""


def create_link_base_js(id2filename):
    s = """

links = %s;

""" % json.dumps(id2filename)
    return s


def create_link_base(id2filename):
    """ Returns a Tag <html> containing the page that is responsible to translate links """
    html = Tag(name='html')
    head = Tag(name='head')
    html.append(head)

    body = Tag(name='body')
    html.append(body)
    s = create_link_base_js(id2filename)
    script = Tag(name='script')
    script.append(s)
    body.append(script)

    script = Tag(name='script')
    script.append(jump_script)
    body.append(script)
    #     pre = Tag(name='pre')
    #     pre.append(str(id2filename))
    #     body.append(pre)
    return html


def do_remove_stuff(soup, remove_selectors, remove):
    all_selectors = []
    if remove is not None and remove != '':
        all_selectors.append(remove)
    if remove_selectors:
        all_selectors.extend(remove_selectors)

    logger.debug('all_selectors: %s' % all_selectors)

    all_removed = ''
    for selector in all_selectors:
        nremoved = 0
        logger.debug('Removing selector %r' % remove)
        toremove = list(soup.select(selector))
        logger.debug('Removing %d objects' % len(toremove))
        for x in toremove:
            nremoved += 1
            nd = len(list(x.descendants))
            logger.debug('removing %s with %s descendants' % (x.name, nd))
            if nd > 1000:
                s = str(x)[:300]
                logger.debug(' it is %s' % s)
            x.extract()

            all_removed += '\n\n' + '-' * 50 + ' chunk %d removed\n' % nremoved
            all_removed += str(x)
            all_removed += '\n\n' + '-' * 100 + '\n\n'

        logger.info('Removed %d elements of selector %r' % (nremoved, remove))

    # TODO: write somewhere else
    # if all_removed:
    #     with open('parts-removed.html', 'w') as f:
    #         f.write(all_removed)


class NoTocPlaceholder(Exception):
    pass


def generate_and_add_toc(soup, raise_error=False, aug=None):
    if aug is None:
        aug = AugmentedResult()
    logger.info('adding toc')
    body = soup.find('body')
    toc = generate_toc(body, aug)

    # logger.info('TOC:\n' + str(toc))
    toc_ul = bs(toc).ul
    if toc_ul is None:
        # empty TOC
        msg = 'Could not find toc.'
        # logger.warning(msg)
        aug.note_error(msg)
        # XXX
    else:
        toc_ul.extract()
        assert toc_ul.name == 'ul'
        toc_ul['class'] = 'toc'  # XXX: see XXX13
        toc_ul['id'] = MCDPManualConstants.MAIN_TOC_ID

        toc_selector = MCDPManualConstants.TOC_PLACEHOLDER_SELECTOR
        tocs = list(body.select(toc_selector))
        if not tocs:
            msg = 'Cannot find any element of type %r to put TOC inside.' % toc_selector
            if raise_error:
                raise NoTocPlaceholder(msg)
            # logger.warning(msg)
            aug.note_error(msg)
        else:
            toc_place = tocs[0]
            toc_place.replaceWith(toc_ul)
