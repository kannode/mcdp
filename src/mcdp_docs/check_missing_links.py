# -*- coding: utf-8 -*-
from collections import OrderedDict

from mcdp.constants import MCDPConstants
from mcdp.logs import logger
from mcdp_docs.location import HTMLIDLocation
from mcdp_docs.manual_constants import MCDPManualConstants
from mcdp_utils_xml import note_error2, Tag
from mcdp_utils_xml.add_class_and_style import has_class

show_debug_message_for_corrected_links = False


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
            other = id2element[ID]
            for e0 in [element, other]:
                note_error2(e0, 'Naming', 'More than one element with id %r.' % ID)
        id2element[element[att]] = element

    if duplicates:
        s = ", ".join(sorted(duplicates))
        msg = '%d duplicated %s found (not errored): %s' % (len(duplicates), att, s)
        logger.error(msg)
    return id2element, duplicates


def check_if_any_href_is_invalid(soup, res, location0, extra_refs=None):
    """
        Checks if references are invalid and tries to correct them.

        also works the magic
    """

    if extra_refs is None:
        extra_refs = Tag(name='div')
    else:
        print('using extra cross refs')

    # let's first find all the IDs
    id2element_current, duplicates = get_id2element(soup, 'id')
    id2element_extra, _  = get_id2element(extra_refs, 'id')
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

                element = id2element[matches[0]]
                # if 'base_url' in element.attrs:
                #     a['href'] = element.attrs['base_url'] + '#' + matches[0]
                # else:
                a['href'] = '#' + matches[0]

                if matches[0] not in id2element_current:
                    msg = 'Using foreign resolve for %s -> %s' % (matches[0], a['href'])
                    logger.info(msg)

                if show_debug_message_for_corrected_links:
                    msg = '%s not found, but corrected in %s' % (href, matches[0])
                    location = HTMLIDLocation.for_element(a, location0)
                    res.note_warning(msg, location)

            else:
                if has_class(a, MCDPConstants.CLASS_IGNORE_IF_NOT_EXISTENT):
                    del a.attrs['href']
                    # logger.warning('ignoring link %s' % a)
                else:
                    msg = 'I do not know what is indicated by the link %r.' % href
                    marker = Tag(name='span')
                    marker.attrs['class'] = 'inside-unknown-link'
                    marker.append(' (unknown ref %s)' % core)
                    a.append(marker)
                    location = HTMLIDLocation.for_element(a, location0)
                    res.note_error(msg, location)

        if ID in duplicates:
            msg = 'More than one element matching %r.' % href
            location = HTMLIDLocation.for_element(a, location0)
            res.note_error(msg, location)


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
