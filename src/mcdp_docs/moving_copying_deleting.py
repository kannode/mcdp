# -*- coding: utf-8 -*-
from mcdp_utils_misc.timing import timeit_wall
from mcdp_utils_xml import note_error2


def move_things_around(soup, raise_if_errors=False):
    """
        Looks for tags like:

            <move-here src="#line_detector2-line_detector_node2-autogenerated"/>

    """
    from mcdp_docs.check_missing_links import get_id2element

    with timeit_wall('getting all IDs'):
        id2element, duplicates = get_id2element(soup, 'id')

    for e in soup.find_all('move-here'):

        if not 'src' in e.attrs:
            msg = 'Expected attribute "src" for element %s' % str(e)
            raise ValueError(msg)

        src = e.attrs['src']

        if not src.startswith('#'):
            msg = 'Expected that attribute "src" started with "#" for element %s.' % str(e)
            raise ValueError(msg)
        nid = src[1:]

        # O(n^2)
        # el = soup.find(id=nid)
        el = id2element.get(nid, None)
        if not el:
            msg = 'move-here: Could not find ID %r.' % nid
            e.name = 'span'
            note_error2(e, "invalid move-here reference", msg)

            if raise_if_errors:
                raise ValueError(msg)
            else:
                continue
        el.extract()
        e.replace_with(el)
