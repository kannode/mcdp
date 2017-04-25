#!/usr/bin/env python
from mcdp_utils_misc.fileutils import create_tmpdir
from mcdp_hdb_mcdp.host_instance import HostInstance
from quickapp.quick_app_base import QuickAppBase 
from mcdp.logs import logger
from mcdp_library.specs_def import specs
from mcdp_hdb_mcdp.library_view import TheContext
from mcdp.exceptions import MCDPException
from quickapp.quick_app import QuickApp
from collections import namedtuple
from copy import deepcopy
import os
import traceback
import shutil
from contracts.utils import indent
import time
from mcdp_utils_misc.duration_hum import duration_compact

__all__ = [
    'load_all_main',
]

class LoadAll(QuickApp):
    """ 
    
        Loads all models found in the repo specified.
    
        %prog  -d <directory> [-f <filter>]
    """

    def define_options(self, params):
        params.add_string('dirname', short='-d', help='Directory for the repo.') 
        params.add_string('filter', short='-f', help='Filter for this name.', default=None)
        params.add_flag('errors_only',  help='Only show errored in the summary')

    def define_jobs_context(self, context):
        options = self.get_options()
        dirname = options.dirname
            
        db_view = db_view_from_dirname(dirname)
        outdir = os.path.join(options.output, 'results')
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        rmtree_only_contents(outdir)
        

        results = {}
        
        for e in iterate_all(db_view):
            if options.filter is not None:
                # case insensitive
                if not options.filter.lower() in e.id.lower():
                    continue
            c = context.comp(process, dirname, e, job_id = e.id)
            results[e.id] = (e, c)

        context.comp(summary, results, outdir, options.errors_only)
        
def rmtree_only_contents(d):
    ''' Removes all the contents but not the directory itself. '''
    
    for the_file in os.listdir(d):
        file_path = os.path.join(d, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): 
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error(e)
            
def db_view_from_dirname(dirname):
    instance = 'instance'
    upstream  = 'master'
    root = create_tmpdir('root')
    repo_git = {}
    repo_local = {'local':dirname}
    hi = HostInstance(instance, upstream, root, repo_git, repo_local)
    
    db_view = hi.db_view
    db_view.set_root()
    return db_view

def summary(results, out, errors_only):
    s = ""
    shelf_name = None
    library_name = None
    spec_name = None
    
    from termcolor import colored 
    c1 = lambda s: colored(s, color='cyan')
    ce = lambda s: colored(s, color='red')
    cok = lambda s: colored(s, color='green')

    
    for _ in sorted(results):
        e, result = results[_]
        if e.shelf_name != shelf_name:
            shelf_name = e.shelf_name
            s += c1('\n Shelf %s' % shelf_name)
        if e.library_name != library_name:
            library_name = e.library_name
            s += c1('\n   Library %s' % library_name)
        if e.spec_name != spec_name:
            spec_name = e.spec_name
            s += c1('\n     %s' % spec_name)
        if result.error_type:
            s += ce('\n     %20s  %s' % (result.error_type, e.thing_name))
            s += '\n' + indent(result.error_string[:200], '       > ')
        else:
            if not errors_only:
                if result.warnings:
                    warnings = result.warnings
                else:
                    warnings = ''
#                 ok = duration_compact(result.cpu)
                ms = 1000 * result.cpu
                ok = '%dms' % ms
                if ms > 1000:
                    ctime = ce
                else:
                    ctime = lambda x:x
                s += ctime('\n     %20s' % ok ) + '   ' + cok('%s   %s' % (e.thing_name, warnings))
                
        if result.error_type:
            fn = os.path.join(out, '%s.txt' % e.id)
            with open(fn, 'w') as f:
                f.write(result.error_string)
            logger.info('wrote %s' % fn)
            
    s += '\n'
    print(s)
    fn = os.path.join(out, 'stats.txt')
    with open(fn,'w') as f:
        f.write(s)
    logger.info('wrote %s' % fn)
        
def process(dirname, e):
    db_view = db_view_from_dirname(dirname)
    e.repo = db_view.repos[e.repo_name]
    e.shelf = e.repo.shelves[e.shelf_name]
    e.library = e.shelf.libraries[e.library_name]
    e.things = e.library.things.child(e.spec_name)
    subscribed_shelves = get_all_shelves(db_view)
    e.context = TheContext(db_view, subscribed_shelves, e.library_name)
    e.mcdp_library = e.context.get_library()
    try:
        context = e.context.child()
        t0 = time.clock()
        e.mcdp_library.load_spec(e.spec_name, e.thing_name, context=context)
        cpu = time.clock() - t0
        error = None
        error_string = None
    except MCDPException as exc:
        error = type(exc).__name__
        error_string = str(exc)
        cpu = None
        #traceback.format_exc(exc)
    if error:
        logger.error(e.id + ' ' + error)
    
    return Result(error_type=error, error_string=error_string, cpu=cpu, warnings=0)

Result = namedtuple('Result', 'error_type error_string warnings cpu')

class EnvironmentMockup(object):
    pass

def get_all_shelves(db_view):
    subscribed_shelves = list()
    
    for repo_name, repo in db_view.repos.items():
        for shelf_name, shelf in repo.shelves.items():
            subscribed_shelves.append(shelf_name)
    return subscribed_shelves

def iterate_all(db_view):
    ''' Yields a sequence of Environment. '''
    e = EnvironmentMockup()
#     subscribed_shelves = get_all_shelves(db_view)
            
    for repo_name, repo in db_view.repos.items():
        e.repo_name = repo_name
                        
        for shelf_name, shelf in repo.shelves.items():
            e.shelf_name = shelf_name
#             e.shelf = shelf
            for library_name, library in shelf.libraries.items():
                e.library_name = library_name
#                 e.library = library
                
#                 e.context = TheContext(db_view, subscribed_shelves, library_name)
#                 e.mcdp_library = e.context.get_library()

                for spec_name in specs:
                    e.spec_name = spec_name
                    things = library.things.child(spec_name)
#                     e.things = things
                    for thing_name, code in things.items():
                        e.thing_name = thing_name
                        e.id = '%s-%s-%s-%s-%s' % (repo_name, shelf_name, library_name, spec_name, thing_name)
                        yield deepcopy(e) 
    
load_all_main = LoadAll.get_sys_main()

if __name__ == '__main__':
    load_all_main()