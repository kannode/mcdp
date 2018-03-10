# -*- coding: utf-8 -*-
from collections import defaultdict, OrderedDict
from contextlib import contextmanager
import os
import shutil
import tempfile

from contracts.utils import check_isinstance
from mcdp import logger

from .fileutils import get_mcdp_tmp_dir, write_data_to_file
from .locate_files_imp import locate_files
from comptests.comptests import get_comptests_output_dir


def remove_tree_contents(dirname):
    """ Removes all under dirname, but not dirname itself. """
    
    for root, dirs, files in os.walk(dirname):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
            
def create_hierarchy(files0):
    """ 
        Creates a temporary directory with the given files 
    
        files = {
            'lib1.mcdplib/poset1': <contents>
        }
    
    """
    
    mcdp_tmp_dir = get_mcdp_tmp_dir()
    prefix = 'create_hierarchy'
    d = tempfile.mkdtemp(dir=mcdp_tmp_dir, prefix=prefix)
#     
#     if True:
#         warnings.warn('Remove from production')
#         d = '/tmp/create_hierarchy'
#         remove_tree_contents(d)
#         logger.warning("using tmp dir " + d)
#         
    write_hierarchy(d, files0)
    return d

def write_hierarchy(where, files0):
    flattened = mockup_flatten(files0)
    for filename, contents in flattened.items():
        check_isinstance(contents, str)
        fn = os.path.join(where, filename)
        write_data_to_file(contents, fn)
#         dn = os.path.dirname(fn)
#         if not os.path.exists(dn):
#             os.makedirs(dn)
#         with open(fn, 'w') as f:
#             f.write(contents)
            
def read_hierarchy(where):
    # read all files
    res = {}
    for filename in locate_files(where,'*'):
        r = os.path.relpath(filename, where)
        res[r] = open(filename).read()
    return unflatten(res)

def mockup_flatten(d): 
    '''
        from
            a:
                b:
                    x
        to 
            'a/b': x
    '''
    res = {}
    for k, v in d.items():
        if isinstance(v, dict):
#             if not v: # empty directory
#                 v = {'.empty':'# empty'}
            x = mockup_add_prefix(k, mockup_flatten(v))
            res.update(x)
                
        else:
            res[k] = v
    return res


def unflatten(x):
    def empty():
        return defaultdict(empty)
    res = empty()
    for fn, data in x.items():
        components = fn.split('/')
        assert len(components) >= 1
        w = res
        while len(components) > 1:
            w = w[components.pop(0)]
        last = components[0]
        w[last] = data
        
    # re-convert to dicts
    def conv(dd):
        if isinstance(dd, defaultdict):
            return dict((k, conv(d)) for k,d in dd.items())
        else:
            return dd
        
    return conv(res)
    
def mockup_add_prefix(prefix, d):
    res = {}
    for k, v in d.items():
        res['%s/%s' % (prefix, k)] = v
    return res

@contextmanager
def with_dir_content(data, use_dir=None):
    """
        data = str -> YAML folder structure
        
        d1:
            f1: |
                contents of f1
    """
    if isinstance(data, str):
        datas = [data]
    elif isinstance(data, list):
        datas = data
    else:
        raise Exception()
    
    
    
    import yaml
    files = OrderedDict()
    for d in datas:
        data_files = mockup_flatten(yaml.load(d))
        files.update(data_files)
    
        
    if use_dir is not None:
        if '/' in use_dir:
            raise Exception(use_dir)
        d = os.path.join(get_comptests_output_dir(), use_dir)
        remove_tree_contents(d)
        write_hierarchy(d, files)
    else:
        d = create_hierarchy(files)
        
    d0 = os.getcwd()
    os.chdir(d)
    try: 
        yield
    finally:
        os.chdir(d0)
        if False:
            shutil.rmtree(d)
        else:
            logger.debug('Not deleting tmp dir %s' % d)
            
        
        
    