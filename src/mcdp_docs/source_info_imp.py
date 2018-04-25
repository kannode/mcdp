# -*- coding: utf-8 -*-
import datetime
import os
import time
from collections import namedtuple

import git
from bs4.element import Tag
from contracts.utils import check_isinstance, raise_wrapped
from mcdp_docs.github_edit_links import NoRootRepo
from mcdp_docs.tocs import LABEL_NAME
from mcdp_utils_misc import memoize_simple, AugmentedResult
from mcdp_utils_xml import bs, to_html_stripping_fragment

from .github_edit_links import get_repo_root
from .manual_constants import MCDPManualConstants
from .manual_join_imp import DocToJoin


# @memoize_simple
def get_repo_object(root):
    repo = git.Repo(root)

    return repo


class NoSourceInfo(Exception):
    pass


SourceInfo = namedtuple('SourceInfo', 'commit author last_modified has_local_modifications')

@memoize_simple
def get_changed_files(repo_root):
    repo = get_repo_object(repo_root)
    diff =repo.head.commit.diff(None)
    changed = list([os.path.realpath(x.a_path) for x in diff.iter_change_type('M')])
    repo.git = None
    print('Changed in %s' % repo_root)
    print "\n".join(changed)
    return changed


@memoize_simple
def get_source_info(filename):
    """ Returns a SourceInfo object or None if the file is not
        part of the repository. """
    try:
        root = get_repo_root(os.path.realpath(filename))
    except NoRootRepo as e:
        msg = 'Could not get root repo for %s' % filename
        raise_wrapped(NoSourceInfo, e, msg, compact=True)
        raise
    repo = get_repo_object(root)
    path = filename
    try:
        commit = repo.iter_commits(paths=path, max_count=1).next()
    except (StopIteration, ValueError) as _e:
        # ValueError: Reference at 'refs/heads/master' does not exist
        msg = 'Could not find commit for %s' % filename
        raise_wrapped(NoSourceInfo, _e, msg, compact=True)
        raise
    author = commit.author
    last_modified = time.gmtime(commit.committed_date)
    last_modified = datetime.datetime.fromtimestamp(time.mktime(last_modified))

    has_local_modifications = os.path.realpath(filename) in get_changed_files(root)


    commit = commit.hexsha
    repo.git = None
    # print('%s last modified by %s on %s ' % (filename, author, last_modified))
    return SourceInfo(commit=commit, author=author, last_modified=last_modified, has_local_modifications=has_local_modifications)


def make_last_modified(files_contents, nmax=100):
    res = AugmentedResult()
    files_contents = [DocToJoin(*x) for x in files_contents]
    files_contents = [_ for _ in files_contents if _.source_info]

    files_contents = list(sorted(files_contents, key=lambda x: x.source_info.last_modified,
                                 reverse=True))

    r = Tag(name='fragment')
    r.append('\n')
    h = Tag(name='h1')
    h.append('Last modified')
    h.attrs['id'] = 'sec:last-modified'
    r.append(h)
    r.append('\n')

    ul = Tag(name='ul')
    ul.append('\n')
    for d in files_contents[:nmax]:
        li = Tag(name='li')
        when = d.source_info.last_modified
        when_s = time.strftime("%a, %b %d", when)
        #          %H:%M
        li.append(when_s)
        li.append(': ')

        hid = get_main_header(bs(d.contents))
        if hid is None:
            what = "File %s" % d.docname
        else:
            what = Tag(name='a')
            what.attrs['href'] = '#' + hid
            what.attrs['class'] = MCDPManualConstants.CLASS_NUMBER_NAME

        li.append(what)
        li.append(' (')
        name = d.source_info.author.name
        li.append(name)
        li.append(')')

        ul.append(li)
        ul.append('\n')

    r.append(ul)
    s = to_html_stripping_fragment(r)
    #     print s

    res.set_result(s)
    return res


def get_first_header_title(soup):
    """ returns attribute label-name """
    for e in soup.find_all(['h1', 'h2', 'h3']):
        if LABEL_NAME in e.attrs:
            return e.attrs[LABEL_NAME]
    return None


def get_main_header(tag):
    """
        Gets an ID to use as reference for the file.
        Returns the first h1,h2,h3 with ID set.
    """
    check_isinstance(tag, Tag)
    #    check_isinstance(s, (str, unicode))
    #    soup = bs(s)
    for e in tag.find_all(['h1', 'h2', 'h3']):
        if 'id' in e.attrs:
            return e.attrs['id']
    return None
