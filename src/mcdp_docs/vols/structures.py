from collections import OrderedDict
from contextlib import contextmanager
import os

from contracts.utils import indent
from mcdp_utils_misc.fileutils import create_tmpdir
from mcdp_utils_misc.locate_files_imp import locate_files
from mcdp_utils_misc.pretty_printing import pretty_print_dict_newlines


class ScriptException(Exception):
    pass


class BuildStatus(object):

    def __init__(self):
        self.variables = OrderedDict()
        self.filesystem = FakeFilesystem()

        self.files = self.variables['files'] = []

    def substitute(self, s):
        s0 = s
        for k, v in self.variables.items():
            t = '$(%s)' % k
            if t in s:
                if isinstance(v, (str, unicode)):
                    s = s.replace(t, v)
                else:
                    msg = 'Could not substitute %r: %r' % (k, v)
                    raise ScriptException(msg)

        if '$(' in s:
            msg = 'Could not find variables to substitute: %r' % s0
            msg += ' known: %s' % list(self.variables)
            raise ScriptException(msg)
        return s

    def __str__(self):
        od = OrderedDict()
        od['variables'] = pretty_print_dict_newlines(self.variables)
        od['filesystem'] = str(self.filesystem)
        return 'BuildStatus\n' + pretty_print_dict_newlines(od)

    def merge(self, bs2):
        self.variables.update(bs2.variables)
        self.filesystem.update(bs2.filesystem)


class FakeFilesystem(object):

    def __init__(self):
        self.files = OrderedDict()

    def update(self, other):
        self.files.update(other.files)

    @contextmanager
    def capture(self):
        d = os.getcwd()
        try:
            d2 = create_tmpdir('fakefilesystem')
            os.chdir(d2)
            yield

            files = locate_files('.', '*', normalize=False)
            for fn in files:
                self.files[fn] = open(fn).read()
        finally:
            os.chdir(d)

    def __str__(self):
        s = 'FakeFilesystem'
        ff = OrderedDict()
        for fn, data in self.files.items():
            ff[fn] = len(data)
        s += '\n' + indent(pretty_print_dict_newlines(ff), '  ')
        return s
