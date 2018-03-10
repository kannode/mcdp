# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import inspect
from mcdp_lang_utils import Where
from mcdp_utils_misc import pretty_print_dict
import os

from contracts import contract
from contracts.interface import location
from contracts.utils import indent

from .github_edit_links import get_repo_root, get_repo_information
from compmake.utils.friendly_path_imp import friendly_path


class Location(object):
    
    __metaclass__ = ABCMeta
    """ 
    
        A Location object represents the location of something in a file.
        
        
        Where(char, line)
        
    """
    
    @abstractmethod
    def get_stack(self):
        """ Returns the set of all locations, including this one. """
        
        
    
class LocationInString(Location):
    
    @contract(where=Where, parent=Location)
    def __init__(self, where, parent):
        self.where = where
        self.parent = parent
    
    def __repr__(self):
        s2 = indent(str(self.where), '  ')
        s2 += '\n\n' + str(self.parent)
        s = 'Location in string'
        s += '\n\n'+indent(s2, '| ')
        return s
    
    def get_stack(self):
        return [self] + self.parent.get_stack()


class LocationUnknown(Location):
    """ We do not know where the thing came from. """
    
    def __init__(self, level=1): # 1 = our caller
        self.caller_location = None # location_from_stack(level)
    
    def __repr__(self):
        return "LocationUnknown"
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
        d = OrderedDict()
        d['filename'] = friendly_path(self.filename)
        if self.github_info is not None:
            d['github'] = self.github_info
        else:
            d['github'] = '(not available)'
        s = "LocalFile"
        s += '\n' + indent(pretty_print_dict(d), '| ')
        return s
    
    def get_stack(self):
        if self.github_info is not None:
            return [self] + self.github_info.get_stack()
        else:
            return [self]


class SnippetLocation(Location):
    
    @contract(original_file=Location)
    def __init__(self, original_file, line, element_id):
        self.original_file = original_file
        self.line = line
        self.element_id = element_id
        
    def __repr__(self):
        d = OrderedDict()
        d['line'] = self.line
        d['element_id'] = self.element_id
        d['original_file'] = self.original_file
        s = "SnippetLocation"
        s += '\n' + indent(pretty_print_dict(d), '| ')
        return s
     
    def get_stack(self):
        return [self] + self.original_file.get_stack()


class GithubLocation(Location):
    
    ''' Represents the location of a file in a Github repository. '''
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
        
        d['org'] = self.org
        d['repo'] = self.repo
        d['path'] = self.path
#         d['blob_url'] = self.blob_url
#         d['edit_url'] = self.edit_url
        d['commit'] = self.commit
        d['branch'] = self.branch
        
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
    except ValueError:
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
    blob_base = repo_base + '/blob/%s' % (branch)
    edit_base = repo_base + '/edit/%s' % (branch)
    
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
    character_end = location(lineno+1, 0, string)-1
    where = Where(string, character, character_end)
    
    lf = LocalFile(filename)
    res = LocationInString(where, lf)
    return res
    