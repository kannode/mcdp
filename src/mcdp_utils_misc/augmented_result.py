from collections import OrderedDict
import inspect
from mcdp import logger

from contracts import contract
from contracts.utils import indent, check_isinstance

from .pretty_printing import pretty_print_dict
import copy


class Note(object):

    def __init__(self, msg, locations=None, stacklevel=0, prefix=()):
        self.msg = msg
        if locations is None: locations = OrderedDict()
        self.locations = OrderedDict(locations)
        stack = inspect.stack()
        self.created_function = stack[1+stacklevel][3]
        module = inspect.getmodule(stack[1+stacklevel][0])
        self.created_module = module.__name__
        self.created_file = module.__file__
        self.prefix = prefix
        
    def __str__(self):
        s = type(self).__name__
        if self.msg:
            s += "\n\n" + indent(self.msg, '  ') + '\n'
        else:
            s += '\n\n   (No messages given) \n'
        if self.locations: 
            s += '\nThese are the locations indicated:\n'
            locations = OrderedDict()
            from mcdp_docs.location import LocationUnknown
            for k,v in self.locations.items():
                if isinstance(v, LocationUnknown):
                    locations[k] = '(location unknown)'
                else:
                    locations[k] = v
            s += '\n' + indent(pretty_print_dict(locations), '  ')
        else:
            s += '\n(No locations provided)'
        s += '\n\nCreated by function %s()' % self.created_function
        s += '\n   in module %s' % self.created_module
#         s += '\n   in file %s' % self.created_file
        # TODO: use Location
        if self.prefix:
            p = "/".join(self.prefix)
            s = indent(s, p + '> ')
        return s
    
class NoteError(Note):
    pass
    
class NoteWarning(Note):
    pass
        
class AugmentedResult(object):
    """ Wraps a result with notes and output. """
    
    def __init__(self):
        """ If result is None => """
        stacklevel = 0
        stack = inspect.stack()
        called_from = stack[1+stacklevel][3]
        self.desc = "Result of %s()" % called_from 
        self.result = None 
        self.notes = []
        self.output = []

    def get_errors(self):
        return [_ for _ in self.notes if isinstance(_, NoteError)]
    def get_warnings(self):
        return [_ for _ in self.notes if isinstance(_, NoteWarning)]
    
    def assert_no_error(self):
        errors = self.get_errors()
        if errors:
            msg = 'We have obtained %d errors.' % len(errors)
            d = OrderedDict()
            for i, e in enumerate(errors):
                d[str(i)] = e
            msg += '\n' + indent(pretty_print_dict(d), ' ')
            raise AssertionError(msg)
        
    def assert_error_contains(self, s):
        """ Asserts that one of the errors contains the string """
        for _ in self.notes:
            if isinstance(_, NoteError):
                ss = str(_)
                if s in ss:
                    return
        msg = 'No error contained the string %r' % s
        raise AssertionError(msg)
    
    def info(self, s):
        self.log.append('info: %s' % s)
        
    def set_result(self, x):
        self.result = x
    
    def get_result(self):
        r = self.result
        if r is None:
            msg = 'Could not get the value of this; the result was None'
            msg += '\n' + indent(self.summary(), '> ')
            raise ValueError(msg) # FIXME
        return r
    
    
    def summary(self):
        s = "AugmentedResult (%s)" % self.desc
#         s += '\n' + indent(self.desc, ': ')
        if self.notes:
            d = OrderedDict()
            for i, note in enumerate(self.notes):
                if isinstance(note, NoteWarning):
                    what = 'Warning'
                elif isinstance(note, NoteError):
                    what = 'Error'
                else: 
                    assert False, note
                
                d['%s %d' % (what, i)] = note
            s += "\n" + indent(pretty_print_dict(d), '| ')
        else:
            s += '\n' + '| (no notes found)'
        return s
    
    def summary_only_errors(self):
        s = "AugmentedResult (%s)" % self.desc
        notes = self.get_errors()
        
        if notes:
            d = OrderedDict()
            for i, note in enumerate(notes):
                d['error %d' % i] = note
            s += "\n" + indent(pretty_print_dict(d), '| ')
        else:
            s += '\n' + '| (no notes found)'
        
        return s
    @contract(note=Note)
    def add_note(self, note):
        self.notes.append(note)
        
    def note_error(self, msg, locations=None):
        logger.error(msg)
        self.add_note(NoteError(msg, locations, stacklevel=1))
    
    def note_warning(self, msg, locations=None):
        logger.warning(msg)
        self.add_note(NoteWarning(msg, locations, stacklevel=1))
        
    @contract(prefix='str|tuple')
    def merge(self, other, prefix=()):
        if isinstance(prefix, str):
            prefix = (prefix,)
        check_isinstance(other, AugmentedResult)
        have = set()
        for n in self.notes:
            have.add(n.msg)
        for note in other.notes:
            if not note.msg in have:
                note2 = copy.deepcopy(note)
                note2.prefix = prefix + note2.prefix
                self.notes.append(note2)
        
        self.output.extend(other.output)
    