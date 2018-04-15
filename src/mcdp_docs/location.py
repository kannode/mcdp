# -*- coding: utf-8 -*-
import inspect
import os
from abc import ABCMeta, abstractmethod
from collections import OrderedDict

from bs4.element import Tag
from contracts import contract
from contracts.interface import location
from contracts.utils import indent
from mcdp_docs.github_edit_links import NoRootRepo
from mcdp_lang_utils import Where
from mcdp_utils_misc import pretty_print_dict

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
        code = Tag(name='code')
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
        code = Tag(name='code')
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

    def __repr__(self):
        s = "In local file %s" % self.filename
        if self.github_info is not None:
            s += '\n\n' + str(self.github_info)
        return s

        # d = OrderedDict()
        # d['filename'] = friendly_path(self.filename)
        # if self.github_info is not None:
        #     d['github'] = self.github_info
        # else:
        #     d['github'] = '(not available)'
        # s = "LocalFile"
        # s += '\n' + indent(pretty_print_dict(d), '| ')
        # return s

    def get_stack(self):
        if self.github_info is not None:
            return [self] + self.github_info.get_stack()
        else:
            return [self]

    def as_html(self, inline=False):
        div = Tag(name='div')
        p = Tag(name='p')
        p.append('Local file ')
        a = Tag(name='a')
        a.attrs['href'] = self.filename
        a.append(self.filename)
        p.append(a)
        p.append('.')
        #        a = Tag(name='a')
        #        a.attrs['href'] = 'edit://' + self.filename
        #        a.append('edit')
        p.append(a)

        div.append(p)
        if self.github_info is not None:
            div.append(self.github_info.as_html(inline=inline))
        return div


class HTMLIDLocation(Location):

    def __init__(self, element_id):
        self.element_id = element_id

    def get_stack(self):
        return [self]

    def as_html(self, inline=False):
        div = Tag(name='div')
        p = Tag(name='p')
        p.append('Jump to ')
        a = Tag(name='a')
        if inline:
            href = '#%s' % self.element_id
        else:
            href = 'link.html#%s' % self.element_id
        a.attrs['href'] = href
        a.append('element in output file')
        p.append(a)
        p.append('.')
        div.append(p)

        return div

    def __repr__(self):
        d = OrderedDict()
        d['element_id'] = self.element_id
        s = "HTMLIDLocation"
        s += '\n' + indent(pretty_print_dict(d), '| ')
        return s


class SnippetLocation(Location):

    @contract(original_file=Location)
    def __init__(self, original_file, line, element_id):
        self.original_file = original_file
        self.line = line
        self.element_id = element_id

    def as_html(self, inline=False):
        div = Tag(name='div')
        p = Tag(name='p')
        p.append('Jump to ')
        a = Tag(name='a')

        if inline:
            href = '#%s' % self.element_id
        else:
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

    def __init__(self, org, repo, path, blob_base, blob_url, branch, commit, edit_url):
        self.org = org
        self.repo = repo
        self.path = path
        self.blob_base = blob_base
        self.blob_url = blob_url
        self.edit_url = edit_url
        self.commit = commit
        self.branch = branch

    def __repr__(self):
        d = OrderedDict()

        # d['org'] = self.org
        d['repo'] = '%s/%s' % (self.org, self.repo)
        d['branch'] = self.branch
        d['path'] = self.path
        #         d['blob_url'] = self.blob_url
        #         d['edit_url'] = self.edit_url
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

    def get_stack(self):
        return [self]


@contract(returns='$GithubLocation|None')
def get_github_location(filename):
    try:
        repo_root = get_repo_root(filename)
    except NoRootRepo:
        # not in Git
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
    blob_base = repo_base + '/blob/%s' % branch
    edit_base = repo_base + '/edit/%s' % branch

    blob_url = blob_base + "/" + relpath
    edit_url = edit_base + "/" + relpath
    return GithubLocation(org=org, repo=repo, path=relpath,
                          blob_base=blob_base, blob_url=blob_url,
                          edit_url=edit_url,
                          branch=branch, commit=commit)


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
