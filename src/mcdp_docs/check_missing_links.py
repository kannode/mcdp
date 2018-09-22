# -*- coding: utf-8 -*-
from collections import OrderedDict

from contracts import indent
from mcdp.constants import MCDPConstants
from mcdp.logs import logger
from mcdp_docs.location import HTMLIDLocation
from mcdp_docs.manual_constants import MCDPManualConstants
from mcdp_utils_xml import Tag, has_class

show_debug_message_for_corrected_links = False


def detect_duplicate_IDs(soup, res):
    from mcdp_docs.manual_join_imp import can_ignore_duplicated_id

    id2element = OrderedDict()
    for element in soup.select('[id]'):
        ID = element.attrs['id']

        if ID in id2element:
            if can_ignore_duplicated_id(element):
                continue
            else:

                # ignore this because it will be triggered for the sister element
                # e.g. fig:howto-mount-motors-video, fig:howto-mount-motors-video-wrap
                if ID.endswith('-wrap'):
                    continue

                msg = 'Repeated use of ID "%s"' % ID
                element.attrs['id'] = ID + '-duplicate-%s' % id(element)
                locations = OrderedDict()
                locations['repeated-use'] = HTMLIDLocation.for_element(element)
                locations['original-use'] = HTMLIDLocation.for_element(id2element[ID])
                res.note_error(msg, locations)
        else:
            id2element[ID] = element


def get_id2element(soup, att):
    id2element = OrderedDict()
    duplicates = set()

    # ignore the maths
    ignore = set()
    for element in soup.select('svg [%s]' % att):  # node with ID below SVG
        ignore.add(element[att])
    for element in soup.select('svg[%s]' % att):  # svg with ID
        ignore.add(element[att])
    for element in soup.select('[%s^="MathJax"]' % att):  # stuff created by MathJax
        ignore.add(element[att])

    for element in soup.select('[%s]' % att):
        ID = element[att]
        if ID in ignore:
            continue
        if ID in id2element:
            duplicates.add(ID)

            if False:
                other = id2element[ID]
                for e0 in [element, other]:
                    # note_error2(e0, 'Naming', 'More than one element with id %r.' % ID)
                    msg = 'More than one element with id %r.' % ID
                    res.note_error(msg, HTMLIDLocation.before_element(e0))
        id2element[element[att]] = element

    if duplicates:
        n = len(duplicates)
        if n > 100:
            duplicates = list(duplicates)[:100]
        s = ", ".join(sorted(duplicates))
        msg = '%d duplicated %s found: %s' % (n, att, s)
        logger.error(msg)
    return id2element, duplicates


def check_if_any_href_is_invalid(soup, res, location0, extra_refs=None,
                                 ignore_ref_errors=False):
    """
        Checks if references are invalid and tries to correct them.

        also works the magic
    """

    if extra_refs is None:
        extra_refs = Tag(name='div')
    # else:
    #     print('using extra cross refs')

    # let's first find all the IDs
    id2element_current, duplicates = get_id2element(soup, 'id')
    id2element_extra, _ = get_id2element(extra_refs, 'id')

    # logger.debug('extra: %s' % list(id2element_extra))
    id2element = {}
    id2element.update(id2element_extra)
    id2element.update(id2element_current)

    for a in soup.select('[href^="#"]'):
        href = a['href']
        assert href.startswith('#')
        ID = href[1:]

        if a.has_attr('class') and "mjx-svg-href" in a['class']:
            msg = 'Invalid math reference (sorry, no details): href = %s .' % href
            location = HTMLIDLocation.for_element(a, location0)
            res.note_error(msg, location)
            continue

        if ID not in id2element:
            # try to fix it

            # if there is already a prefix, remove it
            if ':' in href:
                i = href.index(':')
                core = href[i + 1:]
            else:
                core = ID

            possible = MCDPManualConstants.all_possible_prefixes_that_can_be_implied

            matches = []
            others = []
            for possible_prefix in possible:
                why_not = possible_prefix + ':' + core
                others.append(why_not)
                if why_not in id2element:
                    matches.append(why_not)

            if len(matches) > 1:
                msg = '%s not found, and multiple matches for heuristics (%s)' % (href, matches)
                location = HTMLIDLocation.for_element(a, location0)
                res.note_error(msg, location)

            elif len(matches) == 1:

                # if 'base_url' in element.attrs:
                #     a['href'] = element.attrs['base_url'] + '#' + matches[0]
                # else:
                a.attrs['href'] = '#' + matches[0]

                if matches[0] not in id2element_current:
                    element = id2element[matches[0]]
                    # msg = 'Using foreign resolve for %s -> %s' % (matches[0], a['href'])
                    # logger.info(msg)
                    # a.attrs['href_external'] = element.attrs['base_url'] + '#' + matches[0]
                    a.attrs['href_external'] = element.attrs['url']

                if show_debug_message_for_corrected_links:
                    msg = '%s not found, but corrected in %s' % (href, matches[0])
                    location = HTMLIDLocation.for_element(a, location0)
                    res.note_warning(msg, location)

            else:
                location = HTMLIDLocation.for_element(a, location0)

                if has_class(a, MCDPConstants.CLASS_IGNORE_IF_NOT_EXISTENT):
                    del a.attrs['href']
                    # logger.warning('ignoring link %s' % a)
                elif ignore_ref_errors and 'external' in a.attrs:
                    msg = 'Ignoring external ref %s' % a.attrs['external']
                    res.note_warning(msg, location)
                else:
                    msg = 'I do not know what is indicated by the link %r.' % href
                    marker = Tag(name='span')
                    marker.attrs['class'] = 'inside-unknown-link'
                    marker.append(' (unknown ref %s)' % core)
                    a.append(marker)

                    if ignore_ref_errors:
                        msg2 = 'I will ignore this error because this is the first pass:'
                        msg2 += '\n\n' + indent(msg, ' > ')
                        res.note_warning(msg2, location)
                    else:
                        res.note_error(msg, location)

        if ID in duplicates:
            msg = 'More than one element matching %r.' % href
            location = HTMLIDLocation.for_element(a, location0)
            res.note_error(msg, location)


class MultipleMatches(Exception):
    pass


class NoMatches(Exception):
    pass


def match_ref(ref, id2element):
    if ref in id2element:
        return ref

    # if there is already a prefix, remove it
    if ':' in ref:
        i = ref.index(':')
        core = ref[i + 1:]
    else:
        core = ref

    possible = MCDPManualConstants.all_possible_prefixes_that_can_be_implied

    matches = []
    others = []
    for possible_prefix in possible:
        why_not = possible_prefix + ':' + core
        others.append(why_not)
        if why_not in id2element:
            matches.append(why_not)

    if len(matches) > 1:
        msg = '%s not found, and multiple matches for heuristics (%s)' % (ref, matches)
        raise MultipleMatches(msg)

    elif len(matches) == 1:
        return matches[0]
    else:
        msg = 'Cannot match %r (core=%r).' % (ref, core)
        msg += '\nKnow: %s' % sorted(id2element)
        raise NoMatches(msg)


def fix_subfig_references(soup):
    """
        Changes references like #fig:x to #subfig:x if it exists.
    """
    # FIXME: O(n^2) complexity
    for a in soup.select('a[href]'):
        if a.attrs['href'] is None:
            print('weird: %s' % a)

    for a in soup.select('a[href^="#fig:"]'):
        name = a['href'][1:]

        alternative = 'sub' + name
        #         print('considering if it exists %r' % alternative)
        if list(soup.select('#' + alternative)):
            newref = '#sub' + name
            #             logger.debug('changing ref %r to %r' % (a['href'],newref))
            a['href'] = newref
