import os

from contracts.utils import check_isinstance, raise_desc
from mcdp_library_tests.tests import get_test_library
from mcdp_tests.generation import for_all_source_all
from mcdp_web.editor_fancy.app_editor_fancy_generic import process_parse_request
from mcdp_web.visualization.app_visualization import generate_view_syntax


def filename2spec(filename):  # TODO: move to specs
    """ returns the corresponding spec based on filename """

    _, dot_extension = os.path.splitext(filename)
    extension = dot_extension[1:]
    extension2spec = {}
    for _, spec in specs.items():
        extension2spec[spec.extension] = spec
    spec = extension2spec[extension]
    return spec


@for_all_source_all
def check_editor_response(filename, source, libname):  # @UnusedVariable
    if libname in ['loading_python', 'making']:
        # mcdplib-loading_python-source_mcdp-load1.mcdp-check_editor_response
        # mcdplib-making-source_mcdp-test1.mcdp-check_editor_response
        return
    library = get_test_library(libname)
    string = source
    spec = filename2spec(filename)

    key = ()
    cache = {}
    make_relative = lambda x: x
    res = process_parse_request(library, string, spec, key, cache, make_relative)

    if res['ok']:

        if 'highlight' in res:
            check_isinstance(res['highlight'], unicode)

    else:
        forgive = ['Could not find file', 'DPNotImplementedError']

        if any(_ in res['error'] for _ in forgive):
            pass
        else:
            msg = 'Failed'
            raise_desc(ValueError, msg, source=source, res=res)


@for_all_source_all
def check_generate_view_syntax(filename, source, libname):  # @UnusedVariable
    from mcdp_library.stdlib import get_test_db
    db_view = get_test_db()
    assert len(db_view.repos) == 1
    repo_name = list(db_view.repos)[0]
    library = get_test_library(libname)

    spec = filename2spec(filename)
    thing_name, _ext = os.path.splitext(os.path.basename(filename))
    make_relative = lambda x: x

    class SessionMockup(object):
        def __init__(self):
            pass

        def get_repo_shelf_for_libname(self, libname):  # @UnusedVariable
            for shelf_name, shelf in db_view.repos[repo_name].shelves.items():
                if libname in shelf.libraries:
                    return repo_name, shelf_name
            msg = 'Could not find repo,shelf for library %r.' % libname
            raise Exception(msg)

        def get_subscribed_shelves(self):
            return list(db_view.repos[repo_name].shelves)

    session = SessionMockup()
    repo_name, shelf_name = session.get_repo_shelf_for_libname(libname)

    class EnvironmentMockup(object):
        def __init__(self):
            self.library_name = libname
            self.spec = spec
            self.library = library
            self.session = session
            self.repo_name = repo_name
            self.shelf_name = shelf_name
            self.thing_name = thing_name
            self.thing = source
            self.db_view = db_view

    e = EnvironmentMockup()
    _res = generate_view_syntax(e, make_relative)
