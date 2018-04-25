# -*- coding: utf-8 -*-

import os
import re
from datetime import datetime

from contracts.utils import raise_wrapped
from git.repo.base import Repo
from mcdp_docs.manual_constants import MCDPManualConstants
from mcdp_utils_misc import memoize_simple


class NoRootRepo(Exception):
    pass


@memoize_simple
def get_repo_root(d):
    """ Returns the root of the repo root, or raise ValueError. """
    if os.path.exists(os.path.join(d, '.git')):
        return d
    else:
        parent = os.path.dirname(d)
        if not parent or parent == '/':
            msg = 'Could not find repo root'
            raise NoRootRepo(msg)
        try:
            return get_repo_root(parent)
        except NoRootRepo:
            msg = 'Could not find root repo for "%s"' % d
            raise NoRootRepo(msg)


def add_edit_links2(soup, location):
    from mcdp_docs.location import GithubLocation
    stack = location.get_stack()
    for l in stack:
        if isinstance(l, GithubLocation):
            break
    else:
        return

    for h in soup.findAll(MCDPManualConstants.headers_for_edit_links):
        h.attrs[MCDPManualConstants.ATTR_GITHUB_EDIT_URL] = l.edit_url
        h.attrs[MCDPManualConstants.ATTR_GITHUB_BLOB_URL] = l.blob_url

        delta = datetime.now() - l.last_modified
        days =  delta.days
        h.attrs[MCDPManualConstants.ATTR_GITHUB_LAST_MODIFIED_DAYS] = str(days)
        if l.has_local_modifications:
            h.attrs[MCDPManualConstants.ATTR_HAS_LOCAL_MODIFICATIONS] = 1


class RepoInfoException(Exception):
    pass


@memoize_simple
def get_repo_information(repo_root):
    """ Returns a dictionary with fields branch, commit, org, repo

        Raises RepoInfoException.
    """
    # print('Creating a Repo object for root %s' % repo_root)
    gitrepo = Repo(repo_root)
    try:
        try:
            branch = str(gitrepo.active_branch)
        except TypeError:
            # TypeError: HEAD is a detached symbolic reference as it points
            # to '4bcaf737955277b156a5bacdd80d1805e4b8bb25'
            branch = None

        commit = gitrepo.head.commit.hexsha
        try:
            origin = gitrepo.remotes.origin
        except AttributeError:
            raise ValueError('No remote "origin".')
        url = origin.url
    except ValueError as e:
        msg = 'Could not get branch, commit, url. Maybe the repo is not initialized.'
        raise_wrapped(RepoInfoException, e, msg, compact=True)
        raise

    # now github can use urls that do not end in '.git'
    if 'github' in url and not url.endswith('.git'):
        url += '.git'
    try:
        org, repo = org_repo_from_url(url)
    except NotImplementedError:
        org, repo = None, None

    author_name = gitrepo.head.commit.author.name
    author_email = gitrepo.head.commit.author.email
    committed_date = gitrepo.head.commit.committed_date

    # avoid expensive garbage collection
    gitrepo.git = None
    return dict(branch=branch, commit=commit, org=org, repo=repo,
                committed_date=committed_date,
                author_name=author_name,
                author_email=author_email)


#
# def get_file_information(repo_root, path):
#     commit = repo.iter_commits(paths=blob.path, max_count=1).next()


def org_repo_from_url(url):
    # 'git@host:<org>/<repo>.git'
    pattern = r':(.*)/(.*)\.git'
    # search() = only part of the string
    match = re.search(pattern=pattern, string=url)
    if not match:
        msg = 'Cannot match this url string: %r' % url
        msg += ' with this regexp: %s' % pattern
        raise NotImplementedError(msg)
    org = match.group(1)
    repo = match.group(2)
    return org, repo
