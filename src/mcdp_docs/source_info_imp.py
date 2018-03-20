# -*- coding: utf-8 -*-
from collections import namedtuple
import time

from bs4.element import Tag
import git

from contracts.utils import check_isinstance
from mcdp_docs.github_edit_links import NoRootRepo
from mcdp_utils_misc import memoize_simple
from mcdp_utils_xml import bs, to_html_stripping_fragment

from .github_edit_links import get_repo_root
from .manual_constants import MCDPManualConstants
from .manual_join_imp import DocToJoin


@memoize_simple
def get_repo_object(root):
    repo = git.Repo(root)
    return repo


SourceInfo = namedtuple('SourceInfo', 'commit author last_modified')


def get_source_info(filename):
    """ Returns a SourceInfo object or None if the file is not
        part of the repository. """
    try:
        root = get_repo_root(filename)
    except NoRootRepo:
        return None
    repo = get_repo_object(root)
    path = filename
    try:
        commit = repo.iter_commits(paths=path, max_count=1).next()
    except (StopIteration, ValueError) as _e:
        # ValueError: Reference at 'refs/heads/master' does not exist
        return None
    author = commit.author
    last_modified = time.gmtime(commit.committed_date)
    commit = commit.hexsha
    #print('%s last modified by %s on %s ' % (filename, author, last_modified))
    return SourceInfo(commit=commit, author=author, last_modified=last_modified)


def make_last_modified(files_contents, nmax=100):
    files_contents = [DocToJoin(*x) for x in files_contents]
    files_contents = [_ for _ in files_contents if _.source_info]

    files_contents = list(sorted(files_contents, key=lambda x:x.source_info.last_modified,
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
    return s


def get_first_header_title(soup):
    ''' returns attribute label-name '''
    a = 'label-name'
    for e in soup.find_all(['h1', 'h2', 'h3']):
        if a in e.attrs:
            return e.attrs[a]
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

