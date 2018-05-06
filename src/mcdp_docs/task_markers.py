# -*- coding: utf-8 -*-
from bs4.element import NavigableString, Tag
from mcdp_docs.location import HTMLIDLocation
from mcdp_docs.manual_constants import MCDPManualConstants
from mcdp_utils_misc import Note

from mcdp_utils_xml import add_class, bs


def substitute_task_markers(soup, res, location):
    # XXX: this is really not sure
    for sub, klass in MCDPManualConstants.task_markers.items():
        substitute_task_marker(soup, sub, klass, res, location)

def get_sanitized_copy(element):
    """ Strips all IDs """
    d = bs(str(element))
    if 'id' in d.attrs:
        del d.attrs['id']
    for e in d.descendants:
        if isinstance(e, Tag):
            if 'id' in e.attrs:
                del e.attrs['id']
    for a in d.select('a[href]'):
        del a.attrs['href']
    return d

def create_notes_from_elements(soup, res, location, unique):
    for klass, tag in MCDPManualConstants.classes_that_create_notes.items():
        markers = list(soup.select('.%s' % klass))
        # print('Found %d markers for class %s' % (len(markers), klass))
        for p in markers:
            div = Tag(name='div')
            s = Tag(name='p')
            s.append('The following was marked as "%s".' % klass)
            div.append(s)
            div2 = Tag(name='div')
            div2.attrs['style'] = 'margin: 1em; font-size: 90%; background-color: #eee; border-radius: 5px; padding: 0.5em;'
            # Copy:
            p2 = get_sanitized_copy(p)
            div2.append(p2)
            div.append(div2)

            tags = (tag,)
            note = Note(div, HTMLIDLocation.for_element(p, location, unique=unique), stacklevel=0, tags=tags)
            res.add_note(note)



def substitute_task_marker(soup, sub, klass, res, location):
    for selector in MCDPManualConstants.task_markers_selectors:
        for p in list(soup.select(selector)):
            # print('adding %s to element %s because' % (klass, p))
            substitute_task_marker_p(p, sub, klass, res, location)


def substitute_task_marker_p(p, sub, klass, res, location):
    for element in list(p.descendants):  # use list() otherwise modifying
        if not isinstance(element, NavigableString):
            continue
        s = element.string
        if sub in s:
            add_class(p, klass)
