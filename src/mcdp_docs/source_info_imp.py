# -*- coding: utf-8 -*-
import datetime
import os
import time
from collections import namedtuple, defaultdict

import git
from bs4.element import Tag
from contracts.utils import check_isinstance, raise_wrapped
from mcdp_docs.tocs import LABEL_NAME
from mcdp_utils_misc import memoize_simple, AugmentedResult, logger
from mcdp_utils_xml import bs, to_html_stripping_fragment, gettext

from .manual_constants import MCDPManualConstants
from .manual_join_imp import DocToJoin


# @memoize_simple
def get_repo_object(root):
    repo = git.Repo(root)

    return repo


class NoSourceInfo(Exception):
    pass


SourceInfo = namedtuple('SourceInfo', 'commit author last_modified has_local_modifications header2sourceinfo')


@memoize_simple
def get_changed_files(repo_root):
    repo = get_repo_object(repo_root)
    diff = repo.head.commit.diff(None)
    changed = list([os.path.realpath(x.a_path) for x in diff.iter_change_type('M')])
    repo.git = None
    msg = 'Files changed in %s' % repo_root
    msg += "\n".join(changed)
    logger.debug(msg)
    return changed


@memoize_simple
def get_source_info(filename):
    """ Returns a SourceInfo object or None if the file is not
        part of the repository. """
    from .github_edit_links import get_repo_root, NoRootRepo

    try:
        root = get_repo_root(os.path.realpath(filename))
    except NoRootRepo as e:
        msg = 'Could not get root repo for %s' % filename
        raise_wrapped(NoSourceInfo, e, msg, compact=True)
        raise

    repo = get_repo_object(root)

    try:
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

        hexsha = commit.hexsha

        if MCDPManualConstants.blame_analysis:
            header2sourceinfo = get_blames(repo, commit, path)
        else:
            header2sourceinfo = None

        # print('%s last modified by %s on %s ' % (filename, author, last_modified))
        return SourceInfo(commit=hexsha, author=author, last_modified=last_modified,
                          has_local_modifications=has_local_modifications,
                          header2sourceinfo=header2sourceinfo)
    finally:
        repo.git = None


HeaderIdent = namedtuple('HeaderIdent', 'id_ text')


def get_blames(repo, commit, path):
    from mcdp_docs.mark.markd import render_markdown
    def contains_header(l):
        if not l.startswith('#'):
            return None
        html = bs(render_markdown(l.encode('utf8')))
        for e in html.select('h1,h2,h3,h4,h5,h6'):
            e_id = e.attrs.get('id', None)
            text = gettext(e)
            return HeaderIdent(e_id, text)
        return None

    headers2commits = defaultdict(set)
    current_header = None

    for _commit, lines in repo.blame(commit.hexsha, path):

        for line in lines:
            # who = _commit.author.name
            # print("%s changed these lines: %s" % (who, line))

            header = contains_header(line)
            if header is not None:
                current_header = header
            headers2commits[current_header].add(_commit)

    if None in headers2commits:
        del headers2commits[None]

    header2sourceinfo = {}
    for id_, commits in headers2commits.items():
        youngest = sorted(commits, key=lambda _: time.gmtime(_.committed_date))[-1]
        author = youngest.author
        last_modified = datetime_from_commit_date(youngest.committed_date)
        has_local_modifications = False
        header2sourceinfo[id_] = SourceInfo(commit=youngest.hexsha,
                                            author=author,
                                            last_modified=last_modified,
                                            has_local_modifications=has_local_modifications,
                                            header2sourceinfo=None)
    # print headers2commits
    # print header2sourceinfo
    return header2sourceinfo


def datetime_from_commit_date(commit_date):
    last_modified = time.gmtime(commit_date)
    last_modified = datetime.datetime.fromtimestamp(time.mktime(last_modified))
    return last_modified


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
