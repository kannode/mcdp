# -*- coding: utf-8 -*-
from collections import defaultdict
import os

from compmake.utils.friendly_path_imp import friendly_path
from mcdp_report.gg_utils import check_not_lfs_pointer
from mcdp_utils_misc import locate_files


def collect_by_extension(d):
    fs = locate_files(d, '*')
    ext2filename = defaultdict(list)
    for filename in fs:
        basename = os.path.basename(filename)
        _, ext = os.path.splitext(basename)
        ext2filename[ext] = []
        ext2filename[ext].append(filename)
        
    
    return ext2filename



def check_bad_input_file_presence(d):

    ext2filenames = collect_by_extension(d)
    
    s = '## Filename extensions statistics'
    s += "\nFound in %s:" % friendly_path(d)
    for ext in sorted(ext2filenames, key=lambda k: -len(ext2filenames[k])):
        x = ext if  ext else '(no ext)'
            
        s += '\n %3d  %10s  files' % ( len(ext2filenames[ext]), x)
#     from mcdp import logger
#     logger.info(s)
    
    no_forbidden(ext2filenames)
    check_lfs_checkout(ext2filenames)
    
def no_forbidden(ext2filenames):
    
    def check(ext, msg):
        if ext in ext2filenames:
            msg += '\nOffending files: '
            for f in ext2filenames[ext]:
                msg += '\n  %s ' % friendly_path(f)
        
            raise Exception(msg)
        
    check('.JPG', 'Use lower case "jpg". ')
    check('.jpeg', 'Use "jpg", not "jpeg". ')
    check('.JPEG', 'Use lower case "jpg", not "JPEG". ')
    
def check_lfs_checkout(ext2filenames):
    lfs_extensions = ['.docx', '.pdf', '.xlsx', '.png', '.pptx', '.key',
     '.JPG', '.JPEG', '.jpg', '.PDF' ,'.pdf', '.PNG', '.png']
    for ext in lfs_extensions:
        if ext in ext2filenames:
            for fn in ext2filenames[ext]:
                data = open(fn).read()
                check_not_lfs_pointer(fn, data)
            
   
    
