import copy
import inspect
from collections import OrderedDict

from bs4.element import Tag
from contracts import contract
from contracts.utils import indent, check_isinstance
from mcdp import logger
from mcdp_utils_xml import insert_inset

from .pretty_printing import pretty_print_dict


class Note(object):

    def __init__(self, msg, locations=None, stacklevel=0, prefix=(), tags=()):
        self.msg = msg
        self.tags = tuple(tags)
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

        for tag in self.tags:
            s = Tag(name='span')
            s.attrs['style'] = 'font-size: 70%; font-family: arial; border: solid 1px black; padding: 2px; '
            s.attrs['class'] = 'note-tag'
            s.append(tag)
            div.append(s)

        div.attrs['class'] = 'note'
        container = Tag(name='div')
        if self.msg is not None:
            if isinstance(self.msg, Tag):
                container.append(self.msg)
            else:
                pre = Tag(name='pre')
                pre.append(self.msg)
                container.append(pre)
        else:
            p = Tag(name='p')
            p.append("No message given.")
            container.append(p)
        div.append(container)

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
                # p = Tag(name='p')
                # p.append("Location:")
                # div.append(p)

                location = list(self.locations.values())[0]
                div.append(location.as_html(inline=inline))
        else:
            p = Tag(name='p')
            p.append("(No locations provided)")
            div.append(p)

        from mcdp_utils_xml import stag

        s = Tag(name='span')
        s.append('Created by function ')
        s.append(stag('code', self.created_function))
        s.append(Tag(name='br'))
        s.append(' in module ')
        s.append(stag('code', self.created_module))
        s.append('.')

        p = Tag(name='p')
        p.append(s)
        div.append(s)
        return div


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
        # ne = len(self.get_errors())
        # nw = len(self.get_warnings())
        n = len(self.notes)
        return 'AugmentedResult(%s notes)' % n

    def get_notes_by_tag(self, tag):
        return [_ for _ in self.notes if tag in _.tags]

    def assert_no_error(self):
        from mcdp_docs.manual_constants import MCDPManualConstants
        errors = self.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_ERROR)
        if errors:
            msg = 'We have obtained %d errors.' % len(errors)
            d = OrderedDict()
            for i, e in enumerate(errors):
                d[str(i)] = e
            msg += '\n' + indent(pretty_print_dict(d), ' ')
            raise AssertionError(msg)

    def assert_error_contains(self, s):
        """ Asserts that one of the errors contains the string """
        for _ in self.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_ERROR):
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
                d['tags'] = ",".join(note.tags) 

                d['%s %d' % (what, i)] = note
            s += "\n" + indent(pretty_print_dict(d), '| ')
        else:
            s += '\n' + '| (no notes found)'
        return s


    @contract(note=Note)
    def add_note(self, note):
        self.notes.append(note)

    def note_error(self, msg, locations=None, tags=()):
        from mcdp_docs.manual_constants import MCDPManualConstants
        tags = tuple(tags) + (MCDPManualConstants.NOTE_TAG_ERROR,)
        note = Note(msg, locations, stacklevel=1, tags=tags)
        self.add_note(note)
        logger.error(str(note))

    def note_warning(self, msg, locations=None, tags=()):
        from mcdp_docs.manual_constants import MCDPManualConstants
        tags = tuple(tags) + (MCDPManualConstants.NOTE_TAG_WARNING,)
        note = Note(msg, locations, stacklevel=1, tags=tags)
        self.add_note(note)
        # logger.warn(str(note))

    def note_task(self, msg, locations=None, tags=()):
        from mcdp_docs.manual_constants import MCDPManualConstants
        tags = tuple(tags) + (MCDPManualConstants.NOTE_TAG_TASK,)
        note = Note(msg, locations, stacklevel=1, tags=tags)
        self.add_note(note)

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
    div.error, div.warning, div.task {
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
    div.task {
        border: solid 1px blue;
        color: darkblue;
    }
    """
    s = Tag(name='style')
    s.append(style)
    return s


def html_list_of_notes(aug, tag, how_to_call_them, klass, header=None):
    notes = aug.get_notes_by_tag(tag)
    print('%d notes for tag %s' % (len(notes), tag))
    html = Tag(name='html')
    head = Tag(name='head')
    meta = Tag(name='meta')
    meta.attrs['content'] = "text/html; charset=utf-8"
    meta.attrs['http-equiv'] = "Content-Type"
    head.append(meta)
    html.append(head)
    body = Tag(name='body')
    if header is not None:
        body.append(header)
    html.append(body)
    if not notes:
        p = Tag(name='p')
        p.append('There were no %s.' % how_to_call_them)
        body.append(p)
    else:
        p = Tag(name='p')
        p.append('There were %d %s.' % (len(notes), how_to_call_them))
        body.append(p)

        for i, note in enumerate(notes):
            div = note.as_html()
            div.attrs['class'] = klass
            body.append(div)
    body.append(get_html_style())
    return str(html)


@contract(aug=AugmentedResult)
def mark_in_html(aug, soup):
    """ Marks the errors and warnings in the html soup."""
    from mcdp_docs.manual_constants import MCDPManualConstants

    warnings = aug.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_WARNING)
    errors = aug.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_ERROR)
    tasks = aug.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_TASK)
    warnings_list = list(_mark_in_html_iterate_id_note_with_location(warnings))
    errors_list = list(_mark_in_html_iterate_id_note_with_location(errors))
    tasks_list = list(_mark_in_html_iterate_id_note_with_location(tasks))
    mark_in_html_notes(errors_list, soup, 'error', 'errors.html',
                       [MCDPManualConstants.CLASS_NOTE_ERROR])
    mark_in_html_notes(warnings_list, soup, 'warning', 'warnings.html',
                       [MCDPManualConstants.CLASS_NOTE_WARNING])
    mark_in_html_notes(tasks_list, soup, 'task', 'tasks.html',
                       [MCDPManualConstants.CLASS_NOTE_TASK])


def mark_in_html_notes(notes, soup, note_type, index_url, klasses):
    from mcdp_docs.check_missing_links import get_id2element
    id2element, duplicates = get_id2element(soup, 'id')
    ids_ordered = list(id2element)

    N = len(notes)
    indices = [None for _ in range(len(notes))]
    for i in range(len(notes)):
        eid, note = notes[i]
        if eid in id2element:
            indices[i] = ids_ordered.index(eid)
        else:
            indices[i] = None

    indices = sorted(range(N), key=lambda _: indices[_])

    def idfor(x):
        return 'note-%s-%d' % (note_type, x)

    def linkto(x):
        eid_, _ = notes[indices[x]]
        return '#%s' % eid_

    from mcdp_utils_xml import stag

    # TODO: there is the case where there are multiple notes that refer to the same element..
    for b, i in enumerate(indices):
        eid, note = notes[i]

        element = id2element.get(eid, None)
        if element is None:
            msg = 'Cannot find the element corresponding to ID %r' % eid
            msg += '\n\nI cannot mark this note:'
            msg += '\n\n' + indent(note, '  | ')
            # raise Exception(msg)  # FIXME
            logger.error(msg)
        else:
            if element.name == 'code' and element.parent and element.parent.name == 'pre':
                element = element.parent

            note_html = note.as_html(inline=True)

            inset = insert_inset(element, short=note_type, # XXX
                                   long_error=note_html, klasses=klasses)

            # if note_type == 'error':
            #     inset = note_error2(element, 'error', note_html)
            # elif note_type == 'warning':
            #     # inset = note_error2(element, 'warning', note_html)
            #     inset = note_warning2(element, 'warning', note_html)
            # else:
            #     assert False

            # if inset is not None:
            inset.attrs['id'] = idfor(b)

            summary = inset.find('summary')

            summary.append('\n')
            if b > 0:
                a = Tag(name='a')
                a.attrs['class'] = 'note-navigation'
                a.append('previous ')
                a.attrs['href'] = linkto(b - 1)
                summary.insert(0, a)

            if b < N - 1:
                a = Tag(name='a')
                a.attrs['class'] = 'note-navigation'
                a.append(' next')
                a.attrs['href'] = linkto(b + 1)
                summary.append(a)
            summary.append(' (%d of %s) ' % (b + 1, len(notes)))
            summary.append('\n')
            summary.append(stag('a', 'index', href=index_url))
            summary.append('\n')

            # summary.append(p)


def _mark_in_html_iterate_id_note_with_location(notes):
    from mcdp_docs.location import LocationUnknown
    from mcdp_docs.location import SnippetLocation
    from mcdp_docs.location import HTMLIDLocation
    for _note in notes:
        for location in _note.locations.values():
            if isinstance(location, LocationUnknown):
                continue
            stack = location.get_stack()
            for l in stack:
                if isinstance(l, SnippetLocation):
                    _eid = l.element_id
                    yield _eid, _note
                if isinstance(l, HTMLIDLocation):
                    _eid = l.element_id
                    yield _eid, _note
