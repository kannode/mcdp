# -*- coding: utf-8 -*-
from bs4.element import NavigableString, Tag
from mcdp_docs.location import HTMLIDLocation
from mcdp_docs.manual_constants import MCDPManualConstants
from mcdp_utils_misc import Note

from mcdp_utils_xml import add_class


def substitute_task_markers(soup, res, location):
    for sub, klass in MCDPManualConstants.task_markers.items():
        substitute_task_marker(soup, sub, klass, res, location)

    create_warnings_for_task_markers(soup, res, location)


def create_warnings_for_task_markers(soup, res, location):
    for klass, tag in MCDPManualConstants.classes_that_create_notes.items():
        markers = list(soup.select('.%s' % klass))
        print('Found %d markers for class %s' % (len(markers), klass))
        for p in markers:
            div = Tag(name='div')
            s = Tag(name='p')
            s.append('The following was marked as "%s".' % klass)
            div.append(s)
            div2 = Tag(name='div')
            div2.attrs['style'] = 'margin: 1em; font-size: 50%; background-color: #aaa; padding: 0.5em;'
            div2.append(p)
            div.append(div2)

            tags = (tag,)
            note = Note(div, HTMLIDLocation.for_element(p, location), stacklevel=0, tags=tags)
            res.add_note(note)
            # res.note_task(div, HTMLIDLocation.for_element(p, location))


def substitute_task_marker(soup, sub, klass, res, location):
    for selector in MCDPManualConstants.task_markers_selectors:
        for p in list(soup.select(selector)):
            substitute_task_marker_p(p, sub, klass, res, location)


def substitute_task_marker_p(p, sub, klass, res, location):
    for element in list(p.descendants):  # use list() otherwise modifying
        if not isinstance(element, NavigableString):
            continue
        s = element.string
        if sub in s:
            add_class(p, klass)
