# -*- coding: utf-8 -*-
from collections import OrderedDict

from contracts.utils import indent
from mcdp_docs.location import HTMLIDLocation
from mcdp_docs.manual_constants import MCDPManualConstants

STATUS_ATTR = 'status'
STATUS_UNKNOWN = 'unknown'

allowed_statuses = OrderedDict()

allowed_statuses[STATUS_UNKNOWN] = ''
allowed_statuses['draft'] = 'This is a draft. Drafts are typically hidden from front-facing versions.'
allowed_statuses['beta'] = 'This is ready for review.'

allowed_statuses['ready'] = 'This is ready to be published.'
allowed_statuses['to-update'] = 'This is out-of-date and needs a refresh.'
allowed_statuses['deprecated'] = 'This part is deprecated and will be eventually deleted.'
allowed_statuses['recently-updated'] = 'This part has been recently updated.'


def all_headers(soup):
    headers = MCDPManualConstants.HEADERS_TO_INDEX
    #['h1', 'h2', 'h3', 'h4', 'h5']
    for h in soup.find_all(headers):
        yield h


def check_status_codes(soup, realpath, res, location):
    for h in all_headers(soup):
        if MCDPManualConstants.ATTR_NOTOC in h.attrs:
            continue
        if STATUS_ATTR in h.attrs:
            s = h.attrs[STATUS_ATTR]
            if not s in allowed_statuses:
                msg = 'Invalid status code %r; expected one of %r' % (s, allowed_statuses)
                msg += '\n' + indent(str(h), '  ')
                res.note_error(msg, HTMLIDLocation.for_element(h, location))
        else:
            # Only warn for h1 that are not part:
            if h.name == 'h1' and not 'part:' in h.attrs.get('id', ''):
                if not 'catkin_ws' in realpath:
                    # let's not worry about the Software repo for now
                    h2 = h.__copy__()
                    h2.attrs.pop('github-blob-url', None)
                    h2.attrs.pop('github-edit-url', None)
                    msg = 'Status not found for this header:\n\n  %s' % str(h2)
                    msg += '\n\n in file %s' % realpath
                    msg += '\n\nPlease set the status for all the top-level headers.'
                    msg += '\n\nThe syntax is:\n\n      # My section    {#SECTIONID status=STATUS}'
                    msg += '\n\nThese are the possible choices for the status:\n'
                    for k, v in allowed_statuses.items():
                        if k != STATUS_UNKNOWN:
                            msg += '\n' + indent(v, '', '%23s   ' % ('status=%s' % k))
                    res.note_error(msg, HTMLIDLocation.for_element(h, location))

            h.attrs[STATUS_ATTR] = STATUS_UNKNOWN



def check_lang_codes(soup, res, location):
    for h in all_headers(soup):
        if MCDPManualConstants.LANG_ATTR in h.attrs:
            s = h.attrs[MCDPManualConstants.LANG_ATTR]
            if not s in MCDPManualConstants.allowed_langs:
                msg = 'Invalid lang code %r; expected one of %r' % (s, MCDPManualConstants.allowed_langs)
                msg += '\n' + indent(str(h), '  ')
                # note_error2(h, 'syntax error', msg)
                res.note_error(msg, HTMLIDLocation.for_element(h, location))

