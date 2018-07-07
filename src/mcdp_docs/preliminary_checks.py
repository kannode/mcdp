# -*- coding: utf-8 -*-
import re

from mcdp import MCDPConstants, logger
from mcdp.exceptions import DPSyntaxError
from mcdp_docs.location import LocationInString
from mcdp_lang_utils import Where, location as find_location
from mcdp_utils_misc import format_list

from .latex.latex_preprocess import extract_maths
from .mark.markdown_transform import censor_markdown_code_blocks

__all__ = ['do_preliminary_checks_and_fixes']


def do_preliminary_checks_and_fixes(s, res, location0):
    if MCDPConstants.allow_tabs:
        if '\t' in s:
            i = s.index('\t')
            msg = "Tabs bring despair (e.g. Markdown does not recognize them.)"
            where = Where(s, i)

            location = LocationInString(where, location0)
            # logger.warn(msg + '\n\n' + indent(where, '  '))  # TODO: make augmented result
            res.note_warning(msg, location)
            s = s.replace('\t', ' ' * MCDPConstants.tabsize)
    else:
        check_no_tabs(s)
    check_no_forbidden(s, res, location0)

    s = remove_comments(s)
    s = check_misspellings(s)

    if False:
        check_lists(s, res, location0)

    s = check_most_of_it_xml(s, res, location0)
    return s

def check_lists(s, res, location):
    lines = s.split('\n')
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if line.startswith('- ') or line.startswith('* '):
            previous_empty = lines[i-1].strip() == ''
            if not previous_empty:
                msg = 'It looks like here you wanted to start a list but you did not leave an empty line.'
                col = 0
                line = i
                character = find_location(line, col, s)
                where = Where(s, character)
                res.note_warning(msg, LocationInString(where, location))


def assert_not_contains(s, what):
    if not what in s:
        return
    i = s.index(what)
    if i is not None:
        msg = 'Found forbidden sequence "%s".' % what
        where = Where(s, i, i + len(what))
        raise DPSyntaxError(msg, where=where)


def check_no_tabs(s):
    if '\t' in s:
        i = s.index('\t')
        msg = "Tabs bring despair (e.g. Markdown does not recognize them.)"
        where = Where(s, i)
        raise DPSyntaxError(msg, where=where)


def check_no_forbidden(s, res, location0):
    forbidden = {
        '>=': ['≥'],
        '<=': ['≤'],
        # '>>': ['?']  # added by mistake by Atom autocompletion
    }
    for f in forbidden:
        if f in s:
            msg = 'Found forbidden sequence %r. This will not end well.' % f
            subs = forbidden[f]
            msg += ' Try one of these substitutions: %s' % format_list(subs)
            c = s.index(f)
            where = Where(s, c, c + len(f))
            res.note_error(msg, LocationInString(where, location0))
            # raise DPSyntaxError(msg, where=where)


def remove_comments(s):
    s = re.sub('<!--(.*?)-->', '', s, flags=re.M | re.DOTALL)
    return s


def check_misspellings(s):
    # check misspellings
    misspellings = ['mcpd', 'MCPD']
    for m in misspellings:
        if m in s:
            c = s.index(m)
            msg = 'Typo, you wrote MCPD rather than MCDP.'
            where = Where(s, c, c + len(m))
            raise DPSyntaxError(msg, where=where)
    return s


def fix_tag(m):
    tagname = m.group(1)
    contents = m.group(2)
    #     print('fix_tag recevied : %r %r' %(tagname, contents))
    allow_empty_attributes = MCDPConstants.docs_xml_allow_empty_attributes
    for att in allow_empty_attributes:

        def fix_if_empty(m2):
            #  print('matched tag 1: %r 2: %r' %( m2.group(1), m2.group(2)))
            char = m2.group(2)
            if char is None: char = ''
            if char is None or char != '=':
                return m2.group(1) + '="" ' + char
            else:
                return m2.group(1) + char

        r = '(%s)(.)?' % att
        contents = re.sub(r, fix_if_empty, contents)

    return "<" + tagname + contents + ">"


def fix_empty_attrs(s):
    s = re.sub(r'<(\w+)(.*?)>', fix_tag, s, flags=re.M | re.DOTALL)
    return s


def check_most_of_it_xml(s, res, location0):
    """
    Checks that most of it is XML, except:
    - Markdown code blocks
    - Latex equations (especially &)
    """

    s = fix_empty_attrs(s)

    # remove entities because ET doesnt't like them
    s_ruin = s
    s_ruin, _maths = extract_maths(s_ruin)
    s_ruin = censor_markdown_code_blocks(s_ruin, res, location0)
    s_ruin = re.sub('&#\d+;', 'ENTITY', s_ruin)
    s_ruin = re.sub('&\w+;', 'NAMEDENTITY', s_ruin)

    check_parsable(s_ruin)

    return s


def check_parsable(s):
    from xml.etree import ElementTree as ET
    #     parser = ET.XMLParser()
    #     parser.entity["nbsp"] = unichr(160)
    s = '<add-wrap-for-xml-parser>' + s + '</add-wrap-for-xml-parser>'
    #     print indent(s, ' for xml')
    #     with open('rtmp.xml', 'w') as f:
    #         f.write(s)
    try:
        _ = ET.fromstring(s)
    except Exception as e:
        line1, col1 = e.position
        line = line1 - 1
        col = col1 - 1
        character = find_location(line, col, s)
        msg = 'Invalid XML: %s' % e
        where = Where(s, character)
        logger.error('line %s col %s' % (where.line, where.col))
        logger.error(where)
        raise DPSyntaxError(msg, where=where)
