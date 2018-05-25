# -*- coding: utf-8 -*-
import os
import shutil
import time

from bs4.element import Tag
from contracts.utils import raise_wrapped, indent
from git.exc import GitCommandError, InvalidGitRepositoryError
from git.repo.base import Repo
from mcdp.exceptions import DPSemanticError
from mcdp.logs import logger
from mcdp_docs.location import HTMLIDLocation
from mcdp_utils_misc import locate_files, memoize_simple
from mcdp_utils_xml import add_class

from .reference import parse_github_file_ref, InvalidGithubRef


def substitute_github_refs(soup, defaults, res, location):
    n = 0

    for a in soup.find_all('a'):
        href = a.attrs.get('href', '')
        if href.startswith('github:'):
            substitute_github_ref(a, defaults, res, location)
            n += 1

    return n


class FailedRepos(object):
    failed_repos = {}


def substitute_github_ref(a, defaults, res, location):
    href = a.attrs['href']
    try:
        ref = parse_github_file_ref(href)
    except InvalidGithubRef as e:
        msg = 'Could not parse a reference in %s.' % str(a)
        msg += '\n\n' + indent(e, '  > ')
        res.note_warning(msg, HTMLIDLocation.for_element(a, location))
        return
        # raise_wrapped(DPSyntaxError, e, msg, compact=True)

    if ref.url in FailedRepos.failed_repos:
        msg = 'Skipped because checkout of %s already failed.' % ref.url
        res.note_warning(msg, HTMLIDLocation.for_element(a, location))
        return

    if ref.path is None:
        msg = 'There is no path specified.'
        res.note_warning(msg, HTMLIDLocation.for_element(a, location))
        return
        # raise_desc(DPSyntaxError, e, msg, ref=ref)

    try:
        ref = resolve_reference(ref, defaults)
    except CouldNotResolveRef as e:
        res.note_error(str(e), HTMLIDLocation.for_element(a, location))
        FailedRepos.failed_repos[ref.url] = str(e)
        #     logger.debug(ref.url)
        return

    a.attrs['href'] = ref.url

    if not list(a.children):
        c = Tag(name='code')
        add_class(c, 'github-resource-link')
        c.append(os.path.basename(ref.path))
        a.append(c)


@memoize_simple
def get_all_files(dirname):
    all_files = locate_files(dirname, '*', include_directories=True)
    res = []
    for x in all_files:
        res.append(x)
        if os.path.isdir(x):
            res.append(x + '/')

    return sorted(res)


class CouldNotResolveRef(Exception):
    pass


# noinspection PyProtectedMember
def resolve_reference(ref, defaults):
    for k, v in defaults.items():
        if getattr(ref, k, None) is None:
            ref = ref._replace(**{k: v})

    if ref.branch is None:
        ref = ref._replace(branch='master')

    tmpdir = '/tmp/git_repos'

    try:
        dirname = checkout_repository(tmpdir, ref.org, ref.repo, ref.branch)
    except InvalidGitRepositoryError as e:
        msg = 'Could not check out the repository'
        msg += '\n\n' + indent(str(ref), '  ')
        raise_wrapped(CouldNotResolveRef, e, msg, compact=True)
        raise
    except CouldNotCheckoutRepo as e:
        msg = 'Could not check out the repository'
        raise_wrapped(CouldNotResolveRef, e, msg, compact=True)
        raise
    except OSError as e:
        msg = 'Could not check out the repository'
        msg += '\n\n' + indent(str(ref), '  ')
        raise_wrapped(CouldNotResolveRef, e, msg)
        raise

    # now look for the file
    all_files = get_all_files(dirname)
    matches = []

    def does_match(a, short):
        return a.endswith('/' + short)

    for f in all_files:
        if does_match(f, ref.path):
            matches.append(f)
    if not matches:
        # print "\n".join(all_files)
        msg = 'Could not find reference to file %r.' % ref.path
        msg += '\n checkout in %s' % dirname
        msg += '\n' + str(ref)
        raise CouldNotResolveRef(msg)
    if len(matches) > 1:
        msg = 'Multiple matches for %r.' % ref.path
        msg += '\n' + "\n".join(matches)
        raise CouldNotResolveRef(msg)

    filename = os.path.realpath(matches[0])
    base = os.path.realpath(dirname)
    assert filename.startswith(base)
    rel_filename = filename.replace(base + '/', '')
    github_url = ('https://github.com/%s/%s/blob/%s/%s' %
                  (ref.org, ref.repo, ref.branch, rel_filename))

    if os.path.isdir(filename):
        contents = None
    else:
        contents = open(filename).read()

        # now we can resolve from_text and to_text
        if ref.from_text is not None:
            ref = ref._replace(from_line=which_line(contents, ref.from_text, 0))
        if ref.to_text is not None:
            assert ref.from_line is not None
            tl = which_line(contents, ref.to_text, after_line=ref.from_line)
            ref = ref._replace(to_line=tl)

    if ref.from_line is not None:
        github_url += '#L%d' % (ref.from_line + 1)  # github is 1-based
    if ref.to_line is not None:
        github_url += '-L%d' % (ref.to_line + 1)

    ref = ref._replace(contents=contents)
    ref = ref._replace(url=github_url)
    ref = ref._replace(path=filename)
    return ref


def which_line(contents, fragment, after_line):
    lines = contents.split('\n')
    after = "\n".join(lines[after_line:])
    if fragment not in contents:
        msg = 'Cannot find fragment %r in file after line %d' % (fragment, after_line)
        msg += '\n' + indent(after, '| ')
        raise DPSemanticError(msg)
    i = after.index(fragment)
    line = len(after[:i].split('\n')) - 1
    return line + after_line


class CouldNotCheckoutRepo(Exception):
    pass


def checkout_repository(tmpdir, org, repo, branch):
    if branch is None:
        branch = 'master'
    path = os.path.join(tmpdir, org, repo, branch)
    url = 'git@github.com:%s/%s.git' % (org, repo)

    try:
        if not os.path.exists(path):
            checkout(path, url, branch)
        else:
            m = os.path.getmtime(path)
            age = time.time() - m
            if age < 10 * 60:
                pass
            #                 msg = 'Do not checkout repo if young.'
            #                 logger.debug(msg)
            else:
                #                 msg = 'Checkout repo of  age %s.' % age
                #                 logger.debug(msg)
                repo = Repo(path)
                try:
                    repo.remotes.origin.pull()
                    os.utime(path, None)
                except:
                    pass
        return path
    except GitCommandError as e:
        msg = 'Could not checkout repository %s/%s' % (org, repo)
        msg += '\n using url %s' % url
        raise_wrapped(CouldNotCheckoutRepo, e, msg, compact=True)


def checkout(path, url, branch):
    logger.info('Cloning %s to %s' % (url, path))

    try:
        # ignore LFS files
        env = {'GIT_LFS_SKIP_SMUDGE': '1'}
        repo = Repo.clone_from(url, path, branch=branch, depth=1, env=env)
        logger.info('Clone done.')

        head = repo.create_head(branch)
        head.checkout()
        #         if branch != 'master':
        #             repo.delete_head('master')
        return repo
    except:
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
        except:
            pass
        raise
