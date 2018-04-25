# -*- coding: utf-8 -*-
import inspect
import os
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from datetime import datetime

from bs4.element import Tag
from contracts import contract, check_isinstance
from contracts.interface import location
from contracts.utils import indent
from mcdp_docs import logger
from mcdp_docs.github_edit_links import NoRootRepo
from mcdp_lang_utils import Where
from mcdp_utils_misc import pretty_print_dict
from mcdp_utils_xml import stag

from .github_edit_links import get_repo_root, get_repo_information


class Location(object):
    __metaclass__ = ABCMeta
    """

        A Location object represents the location of something in a file.


        Where(char, line)

    """

    @abstractmethod
    def get_stack(self):
        """ Returns the set of all locations, including this one. """

    def as_html(self, inline=False):
        pre = Tag(name='pre')
        code = Tag(name='span')
        code.attrs['class'] = 'location'
        s = str(self)
        code.append(s)
        pre.append(code)
        return pre


class LocationInString(Location):

    @contract(where=Where, parent=Location)
    def __init__(self, where, parent):
        self.where = where
        self.parent = parent

    def __eq__(self, other):
        return isinstance(other, LocationInString) and \
               (self.where == other.where) and \
               (self.parent == other.parent)

    def __repr__(self):
        s = 'Location in string:'
        s += '\n\n' + indent(str(self.where), '  ')
        s += '\n\n' + str(self.parent)
        return s

    def as_html(self, inline=False):
        div = Tag(name='div')
        pre = Tag(name='pre')
        code = Tag(name='span')
        code.attrs['class'] = 'location'
        code.append(str(self.where))
        pre.append(code)
        div.append(pre)

        div.append(self.parent.as_html(inline=inline))

        return div

    def get_stack(self):
        return [self] + self.parent.get_stack()


class LocationUnknown(Location):
    """ We do not know where the thing came from. """

    def __init__(self, level=1):  # 1 = our caller @UnusedVariable
        self.caller_location = None  # location_from_stack(level)

    def as_html(self, inline=False):
        div = Tag(name='div')
        if inline:
            pass
        else:
            p = Tag(name='p')
            p.append('Location not known more precisely.')
            div.append(p)
        return div

    def __repr__(self):
        return "Location unknown"

    #         d = OrderedDict()
    #         d['caller'] = self.caller_location
    #         s = "LocationUnknown"
    #         s += '\n' + indent(pretty_print_dict(d), '| ')
    #         return s

    def get_stack(self):
        return [self]


class LocalFile(Location):

    def __init__(self, filename):
        self.filename = filename
        self.github_info = get_github_location(filename)
        self.last_local_modification = datetime.fromtimestamp(os.path.getmtime(filename))
        if self.github_info is not None:
            if self.github_info.has_local_modifications:
                msg = 'Local file %s has local modifications' % filename
                logger.debug(msg)

    def __repr__(self):
        s = "In local file %s" % self.filename
        if self.github_info is not None:
            s += '\n\n' + str(self.github_info)
        s += '\n last modification: %s' % self.last_local_modification
        return s

    def get_stack(self):
        if self.github_info is not None:
            return [self] + self.github_info.get_stack()
        else:
            return [self]

    def as_html(self, inline=False):
        div = Tag(name='div')
        p = Tag(name='p')
        p.append('Local file ')
        p.append(Tag(name='br'))
        a = Tag(name='a')
        a.attrs['href'] = self.filename
        a.append(self.filename)
        p.append(a)
        p.append('.')
        #        a = Tag(name='a')
        #        a.attrs['href'] = 'edit://' + self.filename
        #        a.append('edit')

        div.append(p)
        if self.github_info is not None:
            div.append(self.github_info.as_html(inline=inline))
        return div


class HTMLIDLocation(Location):

    @staticmethod
    def for_element(element, parent=None, unique=None):
        from mcdp_docs.tocs import add_id_if_not_present
        add_id_if_not_present(element, unique=unique)
        return HTMLIDLocation(element.attrs['id'], parent)

    def __init__(self, element_id, parent=None):
        self.element_id = element_id
        self.parent = parent

    def get_stack(self):
        if self.parent is not None:
            return [self] + self.parent.get_stack()
        else:
            return [self]

    def as_html(self, inline=False):
        div = Tag(name='div')

        if not inline:
            p = Tag(name='p')
            p.append('Jump to ')
            a = Tag(name='a')
            # if inline:
            #     href = '#%s' % self.element_id
            # else:
            href = 'link.html#%s' % self.element_id
            a.attrs['href'] = href
            a.append('element in output file')
            p.append(a)
            p.append('.')
            div.append(p)

        if self.parent is not None:
            div.append(self.parent.as_html(inline=False))

        return div

    def __repr__(self):

        s = 'Found at element %s' % self.element_id

        if self.parent is not None:
            s += '\n\n' + str(self.parent)
        return s
        #
        # d = OrderedDict()
        # d['element_id'] = self.element_id
        # s = "HTMLIDLocation"
        # s += '\n' + indent(pretty_print_dict(d), '| ')
        # return s


class SnippetLocation(Location):

    @contract(original_file=Location)
    def __init__(self, original_file, line, element_id):
        self.original_file = original_file
        self.line = line
        self.element_id = element_id

    def as_html(self, inline=False):
        div = Tag(name='div')

        if not inline:
            p = Tag(name='p')
            p.append('Jump to ')
            a = Tag(name='a')

            # if inline:
            #     href = '#%s' % self.element_id
            # else:
            href = 'link.html#%s' % self.element_id
            a.attrs['href'] = href
            a.append('element in output file')
            p.append(a)
            p.append('.')
            div.append(p)

        p = Tag(name='p')
        p.append('It happened at line %s of:' % self.line)
        div.append(p)

        div.append(self.original_file.as_html(inline=False))

        return div

    def __repr__(self):
        s = 'In element #%s.' % self.element_id

        s += '\n\nAt line %d of:' % self.line

        s += '\n\n' + str(self.original_file)
        return s

        # d = OrderedDict()
        # d['line'] = self.line
        # d['element_id'] = self.element_id
        # d['original_file'] = self.original_file
        # s = "SnippetLocation"
        # s += '\n' + indent(pretty_print_dict(d), '| ')
        # return s

    def get_stack(self):
        return [self] + self.original_file.get_stack()


class GithubLocation(Location):
    """
        Represents the location of a file in a Github repository.


    """

    def __init__(self, org, repo, path, blob_base, blob_url, branch, commit, edit_url,
                 repo_base, branch_url, commit_url, author, last_modified,
                 has_local_modifications):
        check_isinstance(path, str)
        check_isinstance(branch, str)
        self.org = org
        self.repo = repo
        self.path = path
        self.blob_base = blob_base
        self.blob_url = blob_url
        self.edit_url = edit_url
        self.branch_url = branch_url
        self.commit_url = commit_url
        self.commit = commit
        self.branch = branch
        self.repo_base = repo_base
        self.author = author
        self.last_modified = last_modified
        self.has_local_modifications = has_local_modifications

    def __repr__(self):
        d = OrderedDict()

        # d['org'] = self.org
        d['repo'] = '%s/%s' % (self.org, self.repo)
        d['branch'] = self.branch
        d['path'] = self.path
        #         d['blob_url'] = self.blob_url
        #         d['edit_url'] = self.edit_url
        d['author'] = self.author
        d['last_modified'] = self.last_modified
        d['commit'] = self.commit

        s = "GithubLocation"
        s += '\n' + indent(pretty_print_dict(d), '| ')
        return s

    def indication(self):
        d = OrderedDict()

        d['org'] = self.org
        d['repository'] = '%s/%s' % (self.org, self.repo)
        d['path'] = self.path
        d['branch'] = self.branch
        d['commit'] = self.commit
        d['edit here'] = self.edit_url

        return pretty_print_dict(d)

    def as_html(self, inline=False):
        p = Tag(name='p')

        p.append('File ')
        # p.append(stag('span', self.path))
        p.append(stag('a', self.path, href=self.edit_url))
        p.append(Tag(name='br'))
        p.append(' in repo ')

        repo = '%s/%s' % (self.org, self.repo)
        p.append(stag('a', repo, href=self.repo_base))
        p.append(' branch ')

        # print('branch: %s' % self.branch.__repr__())
        p.append(stag('a', str(self.branch), href=self.branch_url))
        p.append(' commit ')
        p.append(stag('a', self.commit[-8:], href=self.commit_url))
        p.append(Tag(name='br'))
        p.append(' last modified by %s on %s' % (self.author, self.last_modified))
        if self.has_local_modifications:
            t = Tag(name='p')
            t.append('File has local modifications')
            p.append(t)
        return p

    def get_stack(self):
        return [self]


@contract(returns='$GithubLocation|None')
def get_github_location(filename):
    # TODO: detect if the copy is dirty
    if not os.path.exists(filename):
        return None # XXX
    try:
        # need realpath because of relative names, e.g. filename = 'docs/file.md' and the root is at ..
        filename_r = os.path.realpath(filename)
        repo_root = get_repo_root(filename_r)
    except NoRootRepo as e:
        # not in Git
        print('file %s not in Git: %s' % (filename, e))
        return None

    repo_info = get_repo_information(repo_root)
    branch = repo_info['branch']
    commit = repo_info['commit']
    org = repo_info['org']
    repo = repo_info['repo']

    if branch is None:
        branch = 'master'
    # Relative path in the directory
    relpath = os.path.relpath(filename, repo_root)

    repo_base = 'https://github.com/%s/%s' % (org, repo)
    commit_url = repo_base + '/commit/' + commit
    branch_url = repo_base + '/tree/' + branch
    blob_base = repo_base + '/blob/' + branch
    edit_base = repo_base + '/edit/' + branch

    blob_url = blob_base + "/" + relpath
    edit_url = edit_base + "/" + relpath

    from .source_info_imp import get_source_info, NoSourceInfo
    # try:
    try:
        source_info = get_source_info(filename)
    except NoSourceInfo as e:
        logger.error(e)
        return None  # XX
    author = source_info.author
    last_modified = source_info.last_modified
    has_local_modifications = source_info.has_local_modifications


    return GithubLocation(org=org, repo=repo, path=relpath,
                          repo_base=repo_base,
                          blob_base=blob_base, blob_url=blob_url,
                          edit_url=edit_url,
                          branch=branch, commit=commit,
                          commit_url=commit_url,
                          branch_url=branch_url,
                          author=author,
                          has_local_modifications=has_local_modifications,
                          last_modified=last_modified)


def location_from_stack(level):
    """
        level = 0: our caller
        level = 1: our caller's caller
    """
    from inspect import currentframe

    cf = currentframe()

    if level == 0:
        cf = cf.f_back
    elif level == 1:
        cf = cf.f_back.f_back
    elif level == 2:
        cf = cf.f_back.f_back.f_back
    elif level == 3:
        cf = cf.f_back.f_back.f_back.f_back
    else:
        raise NotImplementedError(level)

    assert cf is not None, level

    filename = inspect.getfile(cf)
    if not os.path.exists(filename):
        msg = 'Could not read %r' % filename
        raise NotImplementedError(msg)

    lineno = cf.f_lineno - 1
    string = open(filename).read()
    if not string:
        raise Exception(filename)

    character = location(lineno, 0, string)
    character_end = location(lineno + 1, 0, string) - 1
    where = Where(string, character, character_end)

    lf = LocalFile(filename)
    res = LocationInString(where, lf)
    return res
