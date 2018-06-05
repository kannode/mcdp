# -*- coding: utf-8 -*-
import os

from bs4.element import Tag
from contracts.utils import raise_wrapped, indent
from mcdp.exceptions import DPSemanticError
from mcdp_docs.location import HTMLIDLocation

from .reference import parse_github_file_ref
from .substitute_github_refs_i import resolve_reference, CouldNotResolveRef


def display_files(soup, defaults, res, location, raise_errors):
    n = 0
    for element in soup.find_all('display-file'):
        src = element.attrs.get('src', '').strip()
        element.attrs['src'] = src
        if src.startswith('github:'):
            display_file(element, defaults, res, location, raise_errors)
            n += 1
        else:
            msg = 'Unknown schema %r; I only know "github:".' % src
            if raise_errors:
                raise DPSemanticError(msg)
            else:
                res.note_error(msg, HTMLIDLocation.for_element(element, location))
                # note_error2(element, 'syntax error', msg)
    return n


def display_file(element, defaults, res, location, raise_errors):
    assert element.name == 'display-file'
    assert 'src' in element.attrs
    src = element.attrs['src']
    assert src.startswith('github:')
    ref = parse_github_file_ref(src)

    try:
        ref = resolve_reference(ref, defaults=defaults)
    except CouldNotResolveRef as e:
        msg = 'Could not resolve reference %r' % src
        if raise_errors:
            raise_wrapped(DPSemanticError, e, msg, compact=True)
        else:
            msg += '\n\n' + indent(str(e), '> ')
            # note_error2(element, 'reference error', msg)
            res.note_error(msg, HTMLIDLocation.for_element(element, location))

            return

    lines = ref.contents.split('\n')
    a = ref.from_line if ref.from_line is not None else 0
    b = ref.to_line if ref.to_line is not None else len(lines) - 1
    portion = lines[a:b + 1]
    contents = "\n".join(portion)

    div = Tag(name='div')
    base = os.path.basename(ref.path)
    short = base + '-%d-%d' % (a, b)
    div.attrs['figure-id'] = 'code:%s' % short
    figcaption = Tag(name='figcaption')
    t = Tag(name='code')
    t.append(base)
    a = Tag(name='a')
    a.append(t)
    a.attrs['href'] = ref.url
    figcaption.append(a)
    div.append(figcaption)
    pre = Tag(name='pre')
    code = Tag(name='code')
    pre.append(code)
    code.append(contents)
    div.append(pre)
    element.replace_with(div)
