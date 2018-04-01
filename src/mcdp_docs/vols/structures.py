from collections import OrderedDict
from contextlib import contextmanager
import os

from contracts import contract
from contracts.utils import indent
from mcdp_utils_misc import create_tmpdir, locate_files, pretty_print_dict_newlines, \
    pretty_print_dict
from mcdp_utils_misc.path_utils import expand_all

__all__ = ['FakeFilesystem', 'BuildStatus', 'ScriptException']


class ScriptException(Exception):
    pass


class BuildStatus(object):

    def __init__(self):
        self.variables = OrderedDict()
        self.filesystem = FakeFilesystem()

        self.files = self.variables['files'] = []
        self.resources_dirs = self.variables['resources_dirs'] = []

    def __repr__(self):
        s = 'BuildStatus'
        d = OrderedDict()
        d['variables'] = pretty_print_dict(self.variables, MAX=1000)
        d['filesystem'] = self.filesystem
        t = pretty_print_dict(d)
        s += '\n' + indent(t, '   ')
        return s

    @contract(s=unicode, others=dict)
    def substitute(self, s, others={}):
        if s.startswith('path:'):
            rest = s[len('path:'):]
            s2 = self.substitute(rest, others=others)
            return expand_all(s2)
        s0 = s
        complete = {}
        complete.update(others)
        complete.update(self.variables)
        for k, v in complete.items():
            t = '$(%s)' % k
            if t in s:
                if isinstance(v, (str, unicode)):
                    s = s.replace(t, v)
                else:
                    msg = 'Could not substitute %r: %r' % (k, v)
                    raise ScriptException(msg)

        if '$(' in s:
            msg = 'Could not find variables to substitute: %r' % s0
            msg += ' known: %s' % list(complete)
            msg += ' others: %s' % list(others)
            raise ScriptException(msg)
        return s

    def merge(self, bs2):
        update_dict_careful(self.variables, bs2.variables)
#        self.variables.update(bs2.variables)
        self.filesystem.update(bs2.filesystem)


def update_dict_careful(d1, d2):
    for k, v in d2.items():
        if not k in d1:
            d1[k] = v
        else:
            if isinstance(v, list):
                d1[k].extend(d2[k])
            elif isinstance(v, dict):
                d1[k].update(d2[k])
            else:
                if d1[k] != d2[k]:
                    msg = 'Could not update %s: %s %s' % (k, d1[k], d2[k])
                    raise ValueError(msg)


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
