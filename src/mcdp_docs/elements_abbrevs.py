# -*- coding: utf-8 -*-
from bs4.element import Tag, NavigableString

from mcdp.exceptions import DPSyntaxError
from mcdp_docs.manual_constants import MCDPManualConstants
from mcdp_lang_utils import Where, location as find_location
from mcdp_utils_xml import add_class
from mcdp_docs.location import LocationInString

def other_abbrevs(soup, res, location):
    """
        v, val, value   --> mcdp-value
           pos, poset   --> mcdp-poset
           
        <val>x</val> -> <mcdp-value></mcdp-value>
        <pos>x</pos> -> <mcdp-poset></mcdp-poset>
        
        <s> (strikeout!) -> <span> 
        
        <p>TODO:...</p> -> <div class="todo"><p><span>TODO:</span></p>
    """
    from .task_markers import substitute_task_markers

    other_abbrevs_mcdps(soup, res, location)
    #     other_abbrevs_envs(soup)

    substitute_task_markers(soup, res, location)



def other_abbrevs_mcdps(soup, res, location):
    translate = {
        'v': 'mcdp-value',
        'val': 'mcdp-value',
        'value': 'mcdp-value',
        'pos': 'mcdp-poset',
        'poset': 'mcdp-poset',
        's': 'span',
    }
    for k, v in translate.items():
        for e in soup.select(k):
            e.name = v

def has_special_line_prefix(line):
    for prefix in MCDPManualConstants.special_paragraphs:
        if line.startswith(prefix):
            return prefix
    return None


def check_good_use_of_special_paragraphs(md, res, location0):
    lines = md.split('\n')
    for i in range(1, len(lines)):
        line = lines[i]
        prev = lines[i - 1]

        prefix = has_special_line_prefix(line)
        if prefix:
            if prev.strip():
                msg = ('Wrong use of special paragraph indicator. You have '
                       'to leave an empty line before the special paragraph.')
                c = find_location(i, 1, md)
                c_end = c + len(prefix)
                where = Where(md, c, c_end)
                res.note_error(msg, LocationInString(where, location0))

        # noinspection PyUnreachableCode,PyUnreachableCode
        if False:
            def looks_like_list_item(s):
                if s.startswith('--'):
                    return False
                if s.startswith('**'):
                    return False
                return s.startswith('-') or s.startswith('*')

            if looks_like_list_item(line):
                if prev.strip() and not looks_like_list_item(prev):
                    msg = ('Wrong use of list indicator. You have '
                           'to leave an empty line before the list.')
                    c = location(i, 1, md)
                    c_end = c + 1
                    where = Where(md, c, c_end).with_filename(filename)
                    raise DPSyntaxError(msg, where=where)


def substitute_special_paragraphs(soup, res, location):
    for prefix, klass in MCDPManualConstants.special_paragraphs.items():
        substitute_special_paragraph(soup, prefix, klass, res, location)

    for c in MCDPManualConstants.special_paragraphs_foldable:
        for e in list(soup.select('.%s' % c)):
            details = Tag(name='details')
            add_class(details, c)
            summary = Tag(name='summary')
            summary.append(c)
            details.append(summary)
            rest = e.__copy__()
            details.append(rest)
            e.replace_with(details)


def substitute_special_paragraph(soup, prefix, klass, res, location):
    """ 
        Looks for paragraphs that start with a simple string with the given prefix. 
    
        From:
        
            <p>prefix contents</p>
            
        Creates:
        
            <div class='klass-wrap'><p class='klass'>contents</p></div>
    """
    ps = list(soup.select('p'))
    for p in ps:
        # Get first child
        contents = list(p.contents)
        if not contents:
            continue
        c = contents[0]
        if not isinstance(c, NavigableString):
            continue

        s = c.string
        starts = s.lower().startswith(prefix.lower())
        if not starts:
            continue

        without = s[len(prefix):]
        ns = NavigableString(without)
        c.replaceWith(ns)

        div = Tag(name='div')
        add_class(div, klass + '-wrap')
        add_class(p, klass)
        parent = p.parent
        i = parent.index(p)
        p.extract()
        div.append(p)
        parent.insert(i, div)
