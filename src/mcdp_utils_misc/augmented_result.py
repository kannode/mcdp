import copy
import inspect
from collections import OrderedDict

from bs4.element import Tag
from contracts import contract
from contracts.utils import indent, check_isinstance
from mcdp import logger
from mcdp_utils_xml import stag

from .pretty_printing import pretty_print_dict


class Note(object):

    def __init__(self, msg, locations=None, stacklevel=0, prefix=()):
        self.msg = msg
        if locations is None:
            locations = OrderedDict()
        from mcdp_docs.location import Location
        if isinstance(locations, Location):
            locations = {'location': locations}
        check_isinstance(locations, dict)
        self.locations = OrderedDict(**locations)
        stack = inspect.stack()
        self.created_function = stack[1 + stacklevel][3]
        module = inspect.getmodule(stack[1 + stacklevel][0])
        self.created_module = module.__name__
        self.created_file = module.__file__
        self.prefix = prefix

    def __str__(self):
        s = type(self).__name__
        if self.msg:
            s += "\n\n" + indent(self.msg, '  ') + '\n'
        else:
            s += '\n\n   (No messages given) \n'
        if not self.locations:
            s += '\n(No locations provided)'
        elif len(self.locations) == 1:
            s += str(list(self.locations.values())[0])
        else:
            s += '\nThese are the locations indicated:\n'
            locations = OrderedDict()
            from mcdp_docs.location import LocationUnknown
            for k, v in self.locations.items():
                if isinstance(v, LocationUnknown):
                    locations[k] = '(location unknown)'
                else:
                    locations[k] = v
            s += '\n' + indent(pretty_print_dict(locations), '  ')

        s += '\n\nCreated by function %s()' % self.created_function
        s += '\n   in module %s' % self.created_module
        #         s += '\n   in file %s' % self.created_file
        # TODO: use Location
        if self.prefix:
            p = "/".join(self.prefix)
            s = indent(s, p + '> ')
        return s

    def as_html(self, inline=False):
        div = Tag(name='div')
        div.attrs['class'] = 'note'
        pre = Tag(name='pre')
        if self.msg:
            pre.append(self.msg)
        else:
            pre.append("No messages given.")
        div.append(pre)

        if self.locations:

            if len(self.locations) > 1:
                p = Tag(name='p')
                p.append('These are the locations indicated:')
                div.append(p)

                dl = Tag(name='dl')

                for k, v in self.locations.items():
                    dt = Tag(name='dt')
                    dt.append(k)
                    dl.append(dt)

                    dd = Tag(name='dd')
                    dd.append(v.as_html(inline=inline))
                    dl.append(dd)

                div.append(dl)
            else:
                p = Tag(name='p')
                p.append("Location:")
                div.append(p)

                location = list(self.locations.values())[0]
                div.append(location.as_html(inline=inline))
        else:
            p = Tag(name='p')
            p.append("(No locations provided)")
            div.append(p)

        s = Tag(name='span')
        s.append('Created by function ')
        s.append(stag('code', self.created_function))
        s.append(' in module ')
        s.append(stag('code', self.created_module))
        s.append('.')

        p = Tag(name='p')
        p.append(s)
        div.append(s)
        return div


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
        called_from = stack[1 + stacklevel][3]
        self.desc = "Result of %s()" % called_from
        self.result = None
        self.notes = []
        self.output = []

    def __str__(self):
        ne = len(self.get_errors())
        nw = len(self.get_warnings())
        return 'AugmentedResult(%s err, %s warn, %r)' % (ne, nw, self.result)

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

    # def info(self, s):
    #     self.log.append('info: %s' % s)

    def has_result(self):
        # XXX: this should change
        return self.result is not None

    def set_result(self, x):
        self.result = x

    def get_result(self):
        r = self.result
        if r is None:
            msg = 'Could not get the value of this; the result was None'
            msg += '\n' + indent(self.summary(), '> ')
            raise ValueError(msg)  # FIXME
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

    def html_errors(self):
        notes = self.get_errors()
        html = Tag(name='html')
        head = Tag(name='head')
        meta = Tag(name='meta')
        meta.attrs['content'] = "text/html; charset=utf-8"
        meta.attrs['http-equiv'] = "Content-Type"
        head.append(meta)
        html.append(head)
        body = Tag(name='body')
        html.append(body)
        if not notes:
            p = Tag(name='p')
            p.append('There were no errors.')
            body.append(p)
        else:
            p = Tag(name='p')
            p.append('There were %d errors.' % len(notes))
            body.append(p)

            for i, note in enumerate(notes):
                div = note.as_html()
                div.attrs['class'] = 'error'
                body.append(div)

        body.append(get_html_style())
        return str(html)

    def html_warnings(self):
        notes = self.get_warnings()
        html = Tag(name='html')
        head = Tag(name='head')
        meta = Tag(name='meta')
        meta.attrs['content'] = "text/html; charset=utf-8"
        meta.attrs['http-equiv'] = "Content-Type"
        head.append(meta)
        html.append(head)
        body = Tag(name='body')
        html.append(body)
        if not notes:
            p = Tag(name='p')
            p.append('There were no warnings.')
            body.append(p)
        else:
            p = Tag(name='p')
            p.append('There were %d warnings.' % len(notes))
            body.append(p)

            for i, note in enumerate(notes):
                div = note.as_html()
                div.attrs['class'] = 'warning'
                body.append(div)

        body.append(get_html_style())
        return str(html)

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
        note = NoteError(msg, locations, stacklevel=1)
        self.add_note(note)
        logger.error(str(note))

    def note_warning(self, msg, locations=None):
        note = NoteWarning(msg, locations, stacklevel=1)
        self.add_note(note)
        # logger.warn(str(note))

    @contract(prefix='str|tuple')
    def merge(self, other, prefix=()):
        if isinstance(prefix, str):
            prefix = (prefix,)
        check_isinstance(other, AugmentedResult)
        have = set()
        for n in self.notes:
            have.add(n.msg)

        for note in other.notes:
            if note.msg not in have:
                note2 = copy.deepcopy(note)
                note2.prefix = prefix + note2.prefix
                self.notes.append(note2)

        self.output.extend(other.output)


def get_html_style():
    style = """
    div.error, div.warning {
        border-radius: 10px;
        display: inline-block;
        padding: 1em;

        margin-bottom: 2em;
        margin: 1em;
        
    }
    div.error pre,
    div.warning pre {
        white-space: pre-wrap;
    }
    div.error {
        border: solid 1px red;
        color: darkred;
    }
    div.warning {
        border: solid 1px orange;
        color: darkorange;
    }
    """
    s = Tag(name='style')
    s.append(style)
    return s
