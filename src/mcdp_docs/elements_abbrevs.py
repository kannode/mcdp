# -*- coding: utf-8 -*-
from collections import namedtuple

from bs4.element import Tag, NavigableString
from mcdp.exceptions import DPSyntaxError
from mcdp_docs.location import LocationInString, HTMLIDLocation
from mcdp_docs.manual_constants import MCDPManualConstants
from mcdp_lang_utils import Where, location as find_location
from mcdp_utils_xml import add_class




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


Result = namedtuple('Result', 'element ns prefix rest')


def get_elements_starting_with_string(soup, prefix, names=('p', 'cite')):
    ps = list(soup.find_all(list(names)))
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

        string_rest = s[len(prefix):]

        yield Result(element=p, ns=c, prefix=prefix, rest=string_rest)


def substitute_todo(soup, res, location):
    prefix = "TODO"
    klass = 'todo'
    for r in get_elements_starting_with_string(soup, prefix=prefix):
        # r.ns.replaceWith(r.rest)

        div = Tag(name='div')
        add_class(div, klass + '-wrap')
        add_class(r.element, klass)
        parent = r.element.parent
        i = parent.index(r.element)
        r.element.extract()
        div.append(r.element)
        parent.insert(i, div)

        T = 'for'
        if r.rest.strip().startswith(T):
            after = r.rest[r.rest.index(T) + len(T):]
            if ':' in after:
                i = after.index(':')
                dest = after[:i]

                r.element.attrs['for'] = dest.strip()
            else:
                msg = 'Could not find ":" in "%s"' % after
                res.note_error(msg, HTMLIDLocation.for_element(div, location))


def substitute_assignment(soup, res, location):
    from mcdp_docs.manual_join_imp import split_robustly

    for prefix in MCDPManualConstants.ASSIGNMENTS_PREFIXES:
        for r in list(get_elements_starting_with_string(soup, prefix=prefix)):
            names = split_robustly(r.rest, ",")
            span = format_list_of_names(names)

            rep = Tag(name='p')
            rep.append(prefix)
            rep.append(' ')
            rep.append(span)

            s = Tag(name='span')
            s.attrs['style'] = 'display: none'
            s.append(r.rest.strip())
            s.attrs['class'] = 'assignment'
            r.element.insert_before(s)
            r.element.replace_with(rep)

            add_class(rep, 'assignment') # XXX

def format_name(name):
    ns = Tag(name='span')
    ns.append(name)
    ns.attrs['class'] = 'person-name'
    return ns


def format_list_of_names(names):
    span = Tag(name='span')
    span.attrs['class'] = 'people'
    for i, name in enumerate(names):
        if i > 0:
            span.append(", ")
        ns = format_name(name)
        span.append(ns)
    return span


def substitute_special_paragraphs(soup, res, location):
    substitute_assignment(soup, res, location)

    substitute_todo(soup, res, location)

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
    ps = list(soup.find_all(['p', 'cite']))
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
