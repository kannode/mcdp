# -*- coding: utf-8 -*-
from bs4.element import NavigableString
from mcdp_docs.location import HTMLIDLocation
from mcdp_docs.manual_constants import MCDPManualConstants

from mcdp_utils_xml import add_class


def substitute_task_markers(soup, res, location):
    for sub, klass in MCDPManualConstants.task_markers.items():
        substitute_task_marker(soup, sub, klass, res, location)

    for klass in MCDPManualConstants.classes_that_create_warnings:
        for p in list(soup.select('.%s' % klass)):
            msg = '%s' % klass
            res.note_warning(msg, HTMLIDLocation.for_element(p, location))
        
def substitute_task_marker(soup, sub, klass, res, location):
    for selector in MCDPManualConstants.task_markers_selectors:
        for p in list(soup.select(selector)):
            substitute_task_marker_p(p, sub, klass, res, location)

def substitute_task_marker_p(p, sub, klass, res, location):
    for element in list(p.descendants): # use list() otherwise modifying
        if not isinstance(element, NavigableString):
            continue
        s = element.string
        if sub in s:
            add_class(p, klass)
