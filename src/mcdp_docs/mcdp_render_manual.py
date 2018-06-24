# -*- coding: utf-8 -*-
import logging
import os
import pickle
import sys
import tempfile
from collections import OrderedDict, defaultdict

import yaml
from bs4 import Tag
from compmake import UserError
from compmake.utils.friendly_path_imp import friendly_path
from reprep.utils import natsorted
from system_cmd import system_cmd_result

from contracts import contract, indent, check_isinstance
from contracts.utils import raise_wrapped
from mcdp import logger
from mcdp.constants import MCDPConstants
from mcdp.exceptions import DPSyntaxError
from mcdp_library import MCDPLibrary
from mcdp_library.stdlib import get_test_librarian
from mcdp_utils_misc import expand_all, locate_files, get_md5, write_data_to_file, AugmentedResult, tmpdir, \
    html_list_of_notes, mark_in_html, read_data_from_file
from mcdp_utils_xml import to_html_entire_document, bs_entire_document, add_class, stag, bs, br
from quickapp import QuickApp
from .check_bad_input_files import check_bad_input_file_presence
from .composing.cli import compose_go2, ComposeConfig
from .embed_css import embed_css_files
from .github_edit_links import add_edit_links2, add_last_modified_info
from .location import LocalFile, HTMLIDLocation
from .manual_constants import MCDPManualConstants
from .manual_join_imp import DocToJoin, manual_join, update_refs_
from .minimal_doc import get_minimal_document
from .prerender_math import prerender_mathjax
from .read_bibtex import run_bibtex2html
from .source_info_imp import get_source_info, make_last_modified, NoSourceInfo
from .split import create_split_jobs


class RenderManual(QuickApp):
    """ Renders the PyMCDP manual """

    def define_options(self, params):
        params.add_string('src', help="Directories with all contents; separate multiple entries with a colon.")
        params.add_string('resources', help='Extra directories for resources (but not Markdown). Colon separated.',
                          default='')

        params.add_string('bookshort', help='bookshort')
        params.add_string('output_crossref', help='Crossref', default=None)
        params.add_string('output_file', help='Output file', default=None)
        params.add_string('stylesheet', help='Stylesheet for html version', default=None)
        params.add_string('stylesheet_pdf', help='Stylesheet pdf version', default=None)

        params.add_string('split', help='If given, create split html version at this dir.', default=None)
        params.add_flag('only_refs', help='If given, only create the output refs')
        params.add_int('mathjax', help='Prerender MathJax at the level of each file (requires node)', default=0)
        params.add_string('symbols', help='.tex file for MathJax', default=None)
        params.add_string('permalink_prefix', default=None)
        params.add_string('compose', default=None)
        params.add_string('likebtn', help='site id for likebtn', default=None, )
        params.add_flag('raise_errors', help='If given, fail the compilation on errors')
        params.add_flag('cache')
        params.add_flag('ignore_ref_errors')
        params.add_string('extra_crossrefs', help='Link to extra crossrefs', default=None)
        params.add_flag('wordpress_integration')
        params.add_flag('last_modified', help='Add last modified page')
        params.add_flag('generate_pdf', help='Generate PDF version of code and figures.')
        params.add_string('pdf', help='If given, generate PDF at this path.', default=None)
        params.add_string('remove', help='Remove the items with the given selector'
                                         ' (so it does not mess indexing)',
                          default=None)
        params.add_flag('no_resolve_references')
        params.add_flag('mcdp_settings')

    def define_jobs_context(self, context):
        options = self.get_options()

        logger.info(" ".join(sys.argv))

        if options.mcdp_settings:
            MCDPManualConstants.activate_tilde_as_nbsp = False
            MCDPConstants.softy_mode = False

        logger.setLevel(logging.DEBUG)

        def split_colons(x):
            return [_.strip() for _ in x.split(":") if _ and _.strip()]

        src_dirs = split_colons(options.src)
        resources_dirs = split_colons(options.resources)

        self.info("Src dirs: \n" + "\n -".join(src_dirs))
        self.info("Resources dirs: %s" % resources_dirs)

        raise_errors = options.raise_errors
        # out_dir = options.output
        generate_pdf = options.generate_pdf
        out_split_dir = options.split
        out_pdf = options.pdf
        output_file = options.output_file
        remove = options.remove
        stylesheet = options.stylesheet
        stylesheet_pdf = options.stylesheet_pdf
        symbols = options.symbols
        do_last_modified = options.last_modified
        permalink_prefix = options.permalink_prefix
        compose_config = options.compose
        output_crossref = options.output_crossref
        wordpress_integration = options.wordpress_integration
        ignore_ref_errors = options.ignore_ref_errors
        only_refs = options.only_refs
        likebtn = options.likebtn
        bookshort = options.bookshort
        extra_crossrefs = options.extra_crossrefs
        use_mathjax = True if options.mathjax else False

        logger.info('use mathjax: %s' % use_mathjax)
        logger.info('use symbols: %s' % symbols)

        if symbols is not None:
            symbols = open(symbols).read()

        for s in src_dirs:
            check_bad_input_file_presence(s)

        resolve_references = not options.no_resolve_references

        manual_jobs(context,
                    src_dirs=src_dirs,
                    resources_dirs=resources_dirs,
                    out_split_dir=out_split_dir,
                    output_file=output_file,
                    generate_pdf=generate_pdf,
                    stylesheet=stylesheet,
                    stylesheet_pdf=stylesheet_pdf,
                    bookshort=bookshort,
                    remove=remove,
                    use_mathjax=use_mathjax,
                    raise_errors=raise_errors,
                    symbols=symbols,
                    out_pdf=out_pdf,
                    resolve_references=resolve_references,
                    do_last_modified=do_last_modified,
                    permalink_prefix=permalink_prefix,
                    compose_config=compose_config,
                    output_crossref=output_crossref,
                    wordpress_integration=wordpress_integration,
                    likebtn=likebtn,
                    ignore_ref_errors=ignore_ref_errors,
                    extra_crossrefs=extra_crossrefs,
                    only_refs=only_refs,
                    )


@contract(src_dirs='seq(str)', returns='list(str)')
def get_bib_files(src_dirs):
    """ Looks for .bib files in the source dirs; returns list of filenames """
    return look_for_files(src_dirs, "*.bib")


import requests


def get_cross_refs(src_dirs, permalink_prefix, extra_crossrefs, bookshort, ignore=()):
    res = AugmentedResult()
    files = look_for_files(src_dirs, "crossref.html")
    id2file = {}
    soup = Tag(name='div')

    def add_from_soup(s, f, ignore_alread_present, ignore_if_conflict):
        for img in list(s.find_all('img')):
            img.extract()

        for e in s.select('[base_url]'):
            e['external_crossref_file'] = f

        # Remove the ones with the same base_url
        for e in list(s.select('[base_url]')):
            if e.attrs['base_url'] == permalink_prefix:
                e.extract()

        for e in s.select('[id]'):
            id_ = e.attrs['id']
            if id_ == 'container': continue  # XXX:

            if not 'bookshort' in e.attrs:
                # logger.warning('This element does not have bookshort.')
                pass
            else:
                if bookshort == e.attrs['bookshort']:
                    # logger.warning('Skipping because same bookshort.')
                    continue

            if id_ in id2file:
                if not ignore_alread_present:
                    msg = 'Found two elements with same ID "%s":' % id_
                    msg += '\n %s' % id2file[id_]
                    msg += '\n %s' % f
                    res.note_error(msg)
            else:
                id2file[id_] = f
                e2 = e.__copy__()
                if ignore_if_conflict:
                    e2.attrs['ignore_if_conflict'] = '1'
                soup.append(e2)
                soup.append('\n')

    ignore = [os.path.realpath(_) for _ in ignore]
    for _f in files:
        if os.path.realpath(_f) in ignore:
            msg = 'Ignoring file %r' % _f
            logger.info(msg)
            continue
        logger.info('cross ref file %s' % _f)
        data = open(_f).read()
        if permalink_prefix in data:
            msg = 'skipping own file'
            logger.debug(msg)
            continue
        s = bs(data)
        add_from_soup(s, _f, ignore_alread_present=False, ignore_if_conflict=False)

    if extra_crossrefs is not None:
        logger.info('Reading external refs\n%s' % extra_crossrefs)
        try:
            r = requests.get(extra_crossrefs)
        except Exception as ex:
            msg = 'Could not read external cross reference links'
            msg += '\n  %s' % extra_crossrefs
            msg += '\n\n' + indent(str(ex), ' > ')
            res.note_error(msg)
        else:
            logger.debug('%s %s' % (r.status_code, extra_crossrefs))
            if r.status_code == 404:
                msg = 'Could not read external cross refs: %s' % r.status_code
                msg += '\n url: ' + extra_crossrefs
                msg += '\n This is normal if you have not pushed this branch yet.'
                res.note_warning(msg)
                # logger.error(msg)
            s = bs(r.text)
            add_from_soup(s, extra_crossrefs, ignore_alread_present=True, ignore_if_conflict=True)

    # print soup
    res.set_result(str(soup))
    return res


@contract(src_dirs='seq(str)', returns='list(str)')
def get_markdown_files(src_dirs):
    """ Returns a list of filenames. """
    return look_for_files(src_dirs, "*.md")


def look_for_files(srcdirs, pattern):
    """
        Excludes files with "excludes" in the name.
    """
    results = []
    results_absolute = set()
    for d0 in srcdirs:
        d = expand_all(d0)
        if not os.path.exists(d):
            msg = 'Could not find directory %r' % d
            msg += '\nSearching from directory %r' % os.getcwd()
            raise Exception(msg)

        filenames = locate_files(d, pattern,
                                 followlinks=True,
                                 include_directories=False,
                                 include_files=True,
                                 normalize=False)

        ok = []
        for fn in filenames:
            fn0 = os.path.realpath(fn)
            if 'exclude' in fn0:
                logger.info('Excluding file %r because of string "exclude" in it' % fn)
            else:
                if fn0 in results_absolute:
                    logger.debug('Reached the file %s twice' % fn0)
                    pass
                else:
                    results_absolute.add(fn0)
                    ok.append(fn)

        results.extend(natsorted(ok))

    logger.info('Found %d files with pattern %s in %s' %
                (len(results), pattern, srcdirs))
    return results


@contract(src_dirs='seq(str)')
def manual_jobs(context, src_dirs, resources_dirs, out_split_dir, output_file, generate_pdf, stylesheet,
                stylesheet_pdf,
                bookshort,
                use_mathjax, raise_errors, resolve_references=True,
                remove=None, filter_soup=None, symbols=None,
                out_pdf=None,
                only_refs=False,
                permalink_prefix=None,
                compose_config=None,
                output_crossref=None,
                do_last_modified=False,
                wordpress_integration=False,
                ignore_ref_errors=False,
                likebtn=None,
                extra_crossrefs=None):
    """
        src_dirs: list of sources
        symbols: a TeX preamble (or None)
    """
    #
    # if symbols is not None:
    #     symbols = open(symbols).read()
    if stylesheet_pdf is None:
        stylesheet_pdf = stylesheet
    # outdir = os.path.dirname(out_split_dir)  # XXX
    filenames = get_markdown_files(src_dirs)

    if not filenames:
        msg = "Could not find any file for composing the book."
        raise Exception(msg)

    files_contents = []
    for i, filename in enumerate(filenames):
        if is_ignored_by_catkin(filename):
            logger.debug('Ignoring because of CATKIN_IGNORE: %s' % filename)
            continue
        logger.info('adding document %s ' % friendly_path(filename))

        docname, _ = os.path.splitext(os.path.basename(filename))

        contents = open(filename).read()
        contents_hash = get_md5(contents)[:8]
        # because of hash job will be automatically erased if the source changes
        out_part_basename = '%03d-%s-%s' % (i, docname, contents_hash)
        job_id = '%s-%s-%s' % (docname, get_md5(filename)[:8], contents_hash)

        try:
            source_info = get_source_info(filename)
        except NoSourceInfo as e:
            logger.warn('No source info for %s:\n%s' % (filename, e))
            source_info = None

        for d in src_dirs:
            if filename.startswith(d):
                break
        else:
            msg = "Could not find dir for %s in %s" % (filename, src_dirs)
            raise Exception(msg)

        html_contents = context.comp(render_book, generate_pdf=generate_pdf,
                                     src_dirs=src_dirs + resources_dirs,
                                     data=contents, realpath=filename,
                                     use_mathjax=use_mathjax,
                                     symbols=symbols,
                                     raise_errors=raise_errors,
                                     filter_soup=filter_soup,
                                     ignore_ref_errors=ignore_ref_errors,
                                     job_id=job_id)

        doc = DocToJoin(docname=out_part_basename, contents=html_contents,
                        source_info=source_info)
        files_contents.append(tuple(doc))  # compmake doesn't do namedtuples

    ignore = []
    if output_crossref:
        ignore.append(output_crossref)

    crossrefs_aug = get_cross_refs(resources_dirs, permalink_prefix, extra_crossrefs,
                                   ignore=ignore, bookshort=bookshort)

    bib_files = get_bib_files(src_dirs)

    logger.debug('Found bib files:\n%s' % "\n".join(bib_files))
    if bib_files:
        bib_contents_aug = job_bib_contents(context, bib_files)
        entry = DocToJoin(docname='bibtex', contents=bib_contents_aug, source_info=None)
        files_contents.append(tuple(entry))

    if do_last_modified:
        data_aug = context.comp(make_last_modified, files_contents=files_contents)
        entry = DocToJoin(docname='last_modified', contents=data_aug, source_info=None)
        files_contents.append(tuple(entry))

    root_dir = src_dirs[0]

    template = get_main_template(root_dir, resources_dirs)

    references = OrderedDict()
    #     base_url = 'http://book.duckietown.org/master/duckiebook/pdoc'
    #     for extra_dir in extra_dirs:
    #         res = read_references(extra_dir, base_url, prefix='python:')
    #         references.update(res)

    #     extra = look_for_files(extra_dirs, "*.html")
    #
    #     for filename in extra:
    #         contents = open(filename).read()
    #         docname = os.path.basename(filename) + '_' + get_md5(filename)[:5]
    #         c = (('unused', docname), contents)
    #         files_contents.append(c)

    cs = get_md5((crossrefs_aug.get_result()))[:8]

    joined_aug = context.comp(manual_join, template=template, files_contents=files_contents,
                              stylesheet=None, remove=remove, references=references,
                              resolve_references=resolve_references,
                              crossrefs_aug=crossrefs_aug,
                              permalink_prefix=permalink_prefix,
                              job_id='join-%s' % cs)

    if compose_config is not None:
        try:
            data = yaml.load(open(compose_config).read())  # XXX
            compose_config_interpreted = ComposeConfig.from_yaml(data)
        except ValueError as e:
            msg = 'Cannot read YAML config file %s' % compose_config
            raise_wrapped(UserError, e, msg, compact=True)
        else:
            joined_aug = context.comp(make_composite, compose_config_interpreted, joined_aug)

    joined_aug = context.comp(mark_errors_and_rest, joined_aug)

    if likebtn:
        joined_aug = context.comp(add_likebtn, joined_aug, likebtn)

    if wordpress_integration:
        joined_aug = context.comp(add_related, joined_aug, resources_dirs)

    if output_file is not None:
        context.comp(write, joined_aug, output_file)

    if out_split_dir is not None:

        joined_aug_with_html_stylesheet = context.comp(add_style, joined_aug, stylesheet)

        extra_panel_content = context.comp(get_extra_content, joined_aug_with_html_stylesheet)
        id2filename_aug = context.comp_dynamic(create_split_jobs,
                                               bookshort=bookshort,
                                               data_aug=joined_aug_with_html_stylesheet,
                                               mathjax=True,
                                               preamble=symbols,
                                               extra_panel_content=extra_panel_content,
                                               output_dir=out_split_dir, nworkers=0,
                                               output_crossref=output_crossref,
                                               permalink_prefix=permalink_prefix,
                                               only_refs=only_refs)

        if not only_refs:
            context.comp(write_errors_and_warnings_files, id2filename_aug, out_split_dir)
        context.comp(write_manifest_html, out_split_dir)

    if out_pdf is not None:
        joined_aug_with_pdf_stylesheet = context.comp(add_style, joined_aug, stylesheet_pdf)
        prerendered = context.comp(prerender, joined_aug_with_pdf_stylesheet, symbols=symbols)
        pdf_data = context.comp(render_pdf, prerendered)
        context.comp(write_data_to_file, pdf_data, out_pdf)
        context.comp(write_manifest_pdf, out_pdf)


def write_crossref_info(data, id2filename, output_crossref, permalink_prefix, bookshort, main_headers=[]):
    from mcdp_docs.tocs import LABEL_NAME
    soup = bs_entire_document(data)

    cross = Tag(name='body')

    container = Tag(name='div')
    container.attrs['id'] = 'container'
    cross.append(container)

    for e in soup.select('[%s]' % LABEL_NAME):
        # logger.debug('considering %s' % e)
        if not 'id' in e.attrs:
            continue

        id_ = e.attrs['id']
        if id_.startswith('bib:'):
            # logger.warn('Excluding %r from cross refs' % id_)
            continue

        e2 = get_crossref_copy(e)
        e2.attrs[MCDPManualConstants.ATTR_BASE_URL] = permalink_prefix

        if id_ in id2filename:
            basename = id2filename[id_]

            base = '%s/%s' % (permalink_prefix, basename)
            if id_ in main_headers:
                url = base
            else:
                url = base + '#' + id_
            e2.attrs['url'] = url
            e2.attrs['bookshort'] = bookshort

            # print e2.attrs['url']
            a = Tag(name='a')

            a.attrs['href'] = e2.attrs['url']
            if not 'autoid' in id_:
                code = Tag(name='code')
                code.append(id_)
                a.append(code)
                a.append(' ')
                a.append(br())

            a.append(e2.attrs[LABEL_NAME])
            # e2.insert(0, Tag(name='br'))
            # e2.insert(0, ' ')
            e2.insert(0, a)
        else:
            logger.error('Cannot find url for %s' % id_)

        cross.append('\n\n\n')
        cross.append(e2)

    for img in list(cross.find_all('img')):
        img.extract()

    # print('writing cross ref info')
    html = Tag(name='html')
    html.append(cross)
    head = Tag(name='head')
    style = Tag(name='style')
    style.append(CROSSREF_CSS)
    head.append(style)
    html.append(head)

    script = Tag(name='script')
    script.append(CROSSREF_SCRIPT)
    cross.append(script)
    # XXX: we are doing this multiple times
    write_data_to_file(str(html), output_crossref, quiet=True)


def get_crossref_copy(e):
    e2 = e.__copy__()
    # for a in list(e2.descendants):
    #     if isinstance(a, Tag) and 'id' in a.attrs:
    #         del a.attrs['id']
    for m in list(e2.contents):
        # if isinstance(m, Tag):
        m.extract()
    e2.name = 'p'
    return e2


# language=css
CROSSREF_CSS = """
    .container {
        margin-bottom: 10em;
        border: solid 1px red;
        padding: 1em;
    }
    *[id-short] {
        
    }
    *[id-short] * {
        
    }
"""

# language=javascript
CROSSREF_SCRIPT = """

id2url = {};

var divs = document.querySelectorAll("[id]");
for (var i = 0; i < divs.length; i++) {
    e = divs[i];
    ID = e.getAttribute('id');
    url = e.getAttribute('url');
    id2url[ID] = url;
    console.log(ID + ' -> ' + url);
    
    if(ID.includes(":")) {
        ID2 = ID.split(":")[1];
        id2url[ID2] = url;
        console.log(ID2 + ' -> ' + url);
    }
}



function log(s) {
    console.info(s);
    var p = document.createElement('p');
    p.innerHTML = s;
    parent = document.getElementById('container');
    parent.appendChild(p);
}

if (window.location.hash) {
    hash = window.location.hash;
    hashid = hash.substring(1);
    console.info(hashid);
    if (hashid in id2url) {
        outlink = id2url[hashid];
        log("Redirecting to <a href='" + outlink + "'><code>" + outlink + "</code></a>");
        window.location = outlink;
    } else {
        log("Could not find reference <code>" + hashid + "</code>.");
        log("This means that the text to which it refers has not made it to the master branch yet.");
        log("Or, it might mean that the bot has not compiled and published the new book version yet.");
        log("Note that this is completely normal if you are creating a new section.");
    }
} else {
    log("No hash found");
}
"""


def get_extra_content(aug):
    extra_panel_content = Tag(name='div')
    extra_panel_content.attrs['id'] = 'extra-panel-content'
    # language=html
    html = """
    
<p style='text-align: left'>Show:
    <a id='button-show_status' class='button' onclick='show_status();'>section status</a> 
    <a id='button-show_todos'  class='button' onclick='show_todos();'>errors &amp; todos</a> 
    <a id='button-show_local_changes' class='button' onclick='show_local_changes()'>local changes</a>
    <a id='button-show_recent_changes' class='button' onclick='show_recent_changes()'>recent changes</a>
    <a id='button-show_last_change' class='button' onclick='show_last_change()'>last change</a>
    <a id='button-show_header_change' class='button' onclick='show_header_change()'>in-page changes</a>
    <a id='button-show_feedback' class='button' onclick='show_feedback()'>feedback controls</a>

</p>

<style>
.show_todos #button-show_todos,
.show_status #button-show_status,
.show_local_changes #button-show_local_changes,
.show_recent_changes #button-show_recent_changes,
.show_last_change #button-show_last_change,
.show_header_change #button-show_header_change,
.show_feedback #button-show_feedback
 {
    background-color: #bec9ce;
}
.button {
    border: solid 1px black;
    padding: 3px;
    display: inline-block;
    font-size: smaller;
    font-family: sans-serif;
    cursor: pointer;
}

</style>
<script>

function adjust(klass) {
    if(localStorage.getItem(klass) == 1) {
        console.log('adding ' + klass);
        document.body.classList.add(klass);
    } else {
        console.log('removing ' + klass);
        document.body.classList.remove(klass);
    }
}

function unset(klass) {
     localStorage.setItem(klass, 0);
     adjust(klass);
}

function toggle(klass) { 
    if(localStorage.getItem(klass) == 1) {
        console.log('changing ' + klass + ' 1 to 0 ');
        localStorage.setItem(klass, 0);
    } else { 
        console.log('changing ' + klass + ' 0 to 1 ');
        localStorage.setItem(klass, 1);
    }
}

function show_todos() {
    toggle('show_todos');
    adjust('show_todos');
};

function show_status() {
    toggle('show_status');
    adjust('show_status');
}; 

function show_local_changes() {
    toggle('show_local_changes');
    adjust('show_local_changes');
}; 

function show_header_change(){
    toggle('show_header_change');
    adjust('show_header_change');    
}

function show_recent_changes() {
    unset('show_last_change');
    toggle('show_recent_changes');
    adjust('show_recent_changes');
}; 
function show_last_change() {
    unset('show_recent_changes');
    toggle('show_last_change');
    adjust('show_last_change');
}; 

function show_feedback() { 
    toggle('show_feedback');
    adjust('show_feedback');
}; 


adjust('show_header_change');
adjust('show_todos');
adjust('show_status');
adjust('show_local_changes');
adjust('show_recent_changes');
adjust('show_last_change');
adjust('show_feedback');



document.addEventListener("DOMContentLoaded", function(event) {
    
    details = document.getElementById('build-details');
    v = 'show_controls';
    
    
    current = localStorage.getItem(v);
    console.log('current ' + current)
    if(current == 1) {
        details.setAttribute("open", "");
    } else {
       // e.removeAttribute("open");
    }

    details.addEventListener("toggle", function() {
        
         if(details.open) {
                localStorage.setItem(v, 1);
                console.log("set current to 1");
         } else {
                localStorage.setItem(v, 0);
                console.log("set current to 0");
         }
     });
    
});



</script>
    
    """
    extra_panel_content.append(get_notes_panel(aug))
    extra_panel_content.append(bs(html))
    return extra_panel_content


def mark_errors_and_rest(joined_aug):
    soup = bs_entire_document(joined_aug.get_result())
    mark_in_html(joined_aug, soup)
    res = AugmentedResult()
    res.merge(joined_aug)
    res.set_result(to_html_entire_document(soup))
    return res


def add_related(joined_aug, resources_dirs):
    res = AugmentedResult()
    res.merge(joined_aug)
    soup = bs_entire_document(joined_aug.get_result())
    add_related_(soup, res, resources_dirs)
    res.set_result(to_html_entire_document(soup))
    return res


def add_related_(soup, res, resources_dirs):
    posts, users = get_related(res, resources_dirs)

    add_person_links(soup, users, res)

    tag2posts = defaultdict(list)
    for post in posts.values():
        for tag in post['tags']:
            tag2posts[tag].append(post)

    for section in soup.select('section[id]'):

        level = section.attrs['level']

        id_ = section.attrs['id']
        short = id_.replace(':section', '')
        if 'autoid' in short:
            continue

        if short in tag2posts:
            nfound = len(tag2posts[short])
            # print('found question for %s' % short)
            div = Tag(name='div')
            div.attrs['class'] = 'questions-asked'
            table = Tag(name='table')
            for post in tag2posts[short]:
                url = post['url']
                date = post['date']
                author = post['author']
                title = post['title']

                tr = Tag(name='tr')
                td = Tag(name='td')
                if author is not None:
                    info = users[author]
                    a = Tag(name='a')
                    a.append(info['name'])
                    td.append(a)
                tr.append(td)

                td = Tag(name='td')
                td.append(date.strftime("%B %d, %Y"))
                tr.append(td)

                td = Tag(name='td')
                if author is not None:
                    a = Tag(name='a')
                    a.attrs['href'] = url
                    a.append(title)
                    td.append(a)
                tr.append(td)

                table.append(tr)

            div.append(table)
            section.append(div)
        else:
            nfound = 0
            pass
            # print('no questions for %s' % short)

        if level not in ['sec']:
            continue

        p = Tag(name='p')
        p.attrs['class'] = 'questions-prompt'
        a = Tag(name='a')
        a.attrs['href'] = 'http://www2.duckietown.org/questions/ask/?pred=%s' % short
        if nfound == 0:
            p.append("No questions found. You can ask a question ")
            a.append("on the website")
            p.append(a)
            p.append('.')
        else:
            a.append("Ask another question about this section.")
            p.append(a)

        section.append(p)


def find_user_by_name(users, name):
    for k, user in users.items():
        if user['name'] == name:
            return k
    raise KeyError(name)


def add_person_links(soup, users, res):
    if not MCDPManualConstants.add_person_links:
        return

    for span in soup.select('span.person-name'):
        name = span.text

        try:
            k = find_user_by_name(users, name)
            span.name = 'a'
            span.attrs['href'] = users[k]['user_url']
        except KeyError:
            msg = u'Could not find user "%s" in DB.' % name
            res.note_warning(msg.encode('utf8'), HTMLIDLocation.for_element(span))


def get_related(res, resources_dirs):
    filenames = []
    for rd in resources_dirs:
        filenames.extend(locate_files(rd, '*.related.yaml'))

    users = {}
    posts = {}
    for f in filenames:
        location = LocalFile(f)
        contents = open(f).read()
        data = yaml.load(contents)
        # print(indent(data, os.path.basename(f) + ' > '))
        if not isinstance(data, dict):
            msg = 'YAML is None'
            res.note_error(msg, location)
            continue
        if not 'users' in data or not 'posts' in data:
            msg = 'Could not find keys in dict: %s' % list(data)
            res.note_error(msg, location)
        users.update(data['users'])
        posts.update(data['posts'])

    return posts, users


def add_likebtn(joined_aug, likebtn):
    res = AugmentedResult()
    res.merge(joined_aug)
    soup = bs_entire_document(joined_aug.get_result())
    add_likebtn_(soup, likebtn)
    res.set_result(to_html_entire_document(soup))
    return res


def add_likebtn_(soup, likebtn_site_id):
    sections = 'h1[id],h2[id]'

    for h in list(soup.select(sections)):
        id_ = h.attrs['id']

        div = Tag(name='div')
        div.attrs['class'] = 'like_buttons'
        div.append('Please provide your feedback: ')

        tag = Tag(name='span')
        tag.attrs['class'] = 'likebtn-wrapper'
        tag.attrs['data-identifier'] = 'btn-%s' % id_
        tag.attrs['data-site_id'] = likebtn_site_id

        t = tag.attrs
        t['data-theme'] = "tick"
        t['data-white_label'] = "true"
        t['data-white_label'] = "true"
        t['data-identifier'] = "f1-%s" % id_
        t['data-show_dislike_label'] = "true"
        t['data-icon_like_show'] = "false"
        t['data-icon_dislike_show'] = "false"
        t['data-counter_type'] = "percent"
        # t['data-popup_disabled'] = "true"
        t['data-popup_dislike'] = "true"
        t['data-popup_position'] = "bottom"
        t['data-popup_html'] = "Thanks for the feedback!"
        t['data-share_enabled'] = "false"
        t['data-share_size'] = "small"
        t['data-item_url'] = "item-url"
        t['data-item_title'] = 'title'
        t['data-item_description'] = "item - description"
        t['data-item_image'] = "item-image"
        t['data-lazy_load'] = "true"
        t['data-event_handler'] = "callback"
        t['data-i18n_like'] = "Great work!"
        t['data-i18n_dislike'] = "This needs more improvement"
        # t['data-i18n_after_like'] = "Glad you liked it!"
        # t['data-i18n_after_dislike'] = "Please help us improve!"
        t['data-i18n_like_tooltip'] = "This is great content"
        t['data-i18n_dislike_tooltip'] = "Something does not feel right"
        # t['data-i18n_unlike_tooltip'] = "dislike - tooltip - after"
        # t['data-i18n_undislike_tooltip'] = "dislike - tooltip - after"
        t['data-i18n_share_text'] = "Share this content"

        script = bs(likebtn_code).script
        div.append(tag)
        div.append(script)

        h.insert_after(div)


# language=html
likebtn_code = """
<script> 
(function(d, e, s){
    if (d.getElementById("likebtn_wjs"))
        return;
        a = d.createElement(e);
        m = d.getElementsByTagName(e)[0];
        a.async = 1;
        a.id = "likebtn_wjs";
        a.src = s;
        m.parentNode.insertBefore(a, m)}
)(document, "script", "http://w.likebtn.com/js/w/widget.js"); 
</script>
"""


def add_style(data_aug, stylesheet):
    soup = bs_entire_document(data_aug.get_result())
    head = soup.find('head')
    assert head is not None
    link = Tag(name='link')
    link['rel'] = 'stylesheet'
    link['type'] = 'text/css'
    from mcdp_report.html import get_css_filename
    link['href'] = get_css_filename('compiled/%s' % stylesheet)
    head.append(link)
    html = to_html_entire_document(soup)
    res = AugmentedResult()
    res.merge(data_aug)
    res.set_result(html)
    return res


def make_composite(compose_config, joined_aug):
    data = joined_aug.get_result()
    soup = bs_entire_document(data)
    recipe = compose_config.recipe
    remove_status = compose_config.remove_status
    show_removed = compose_config.show_removed
    permalink_prefix = compose_config.purl_prefix
    aug = compose_go2(soup, recipe, permalink_prefix, remove_status, show_removed)
    soup = aug.get_result()
    results = str(soup)
    res = AugmentedResult()
    res.merge(joined_aug)
    res.merge(aug)
    res.set_result(results)
    return res


def prerender(joined_aug, symbols):
    joined = joined_aug.get_result()
    soup = bs_entire_document(joined)
    for details in soup.select('details'):
        details.name = 'div'
        add_class(details, 'transmuted-details')
        # details.attrs['open'] = 1

    joined = to_html_entire_document(soup)
    res = AugmentedResult()
    result = prerender_mathjax(joined, symbols=symbols, res=res)
    res.set_result(result)
    return res


def render_pdf(data_aug):
    data = data_aug.get_result()
    prefix = 'prince_render'
    with tmpdir(prefix=prefix) as d:
        f_html = os.path.join(d, 'file.html')
        with open(f_html, 'w') as f:
            f.write(data)

        f_out = os.path.join(d, 'out.pdf')
        cmd = ['prince', '--javascript', '-o', f_out, f_html]
        pwd = os.getcwd()
        system_cmd_result(
                pwd, cmd,
                display_stdout=False,
                display_stderr=False,
                raise_on_error=True)

        with open(f_out) as f:
            data = f.read()

        return data


def get_notes_panel(aug):
    s = Tag(name='div')
    s.attrs['class'] = 'notes-panel'
    nwarnings = len(aug.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_WARNING))
    ntasks = len(aug.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_TASK))
    nerrors = len(aug.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_ERROR))
    s.append(stag('a', '%d errors' % nerrors, href='errors.html', _class='notes-panel-errors'))
    s.append(', ')
    s.append(stag('a', '%d warnings' % nwarnings, href='warnings.html', _class='notes-panel-errors'))
    s.append(', ')
    s.append(stag('a', '%d tasks' % ntasks, href='tasks.html', _class='notes-panel-errors'))
    return s


def write_errors_and_warnings_files(aug, d):
    if aug.has_result():
        li = aug.get_result()

        from mcdp_docs import LinkInfo
        check_isinstance(li, LinkInfo)

        # id2filename = li.id2filename
    else:
        msg = 'pass aug does not have a result'
        logger.debug(aug.summary())
        raise Exception(msg)

    assert isinstance(aug, AugmentedResult)
    aug.update_refs(li.id2filename)

    header = get_notes_panel(aug)

    manifest = []
    nwarnings = len(aug.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_WARNING))
    fn = os.path.join(d, 'warnings.html')

    html = html_list_of_notes(aug, MCDPManualConstants.NOTE_TAG_WARNING, 'warnings', 'warning', header=header)
    update_refs_('warnings', html, li.id2filename, li.main_headers)

    write_data_to_file(str(html), fn, quiet=True)
    if nwarnings:
        manifest.append(dict(display='%d warnings' % nwarnings,
                             filename='warnings.html'))
        msg = 'There were %d warnings: %s' % (nwarnings, fn)
        logger.warn(msg)

    ntasks = len(aug.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_TASK))
    fn = os.path.join(d, 'tasks.html')

    html = html_list_of_notes(aug, MCDPManualConstants.NOTE_TAG_TASK, 'tasks', 'task', header=header)
    update_refs_('tasks', html, li.id2filename, li.main_headers)
    write_data_to_file(str(html), fn, quiet=True)
    if nwarnings:
        manifest.append(dict(display='%d tasks' % ntasks,
                             filename='tasks.html'))
        msg = 'There are %d open tasks: %s' % (ntasks, fn)
        logger.info(msg)

    nerrors = len(aug.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_ERROR))
    fn = os.path.join(d, 'errors.html')
    html = html_list_of_notes(aug, MCDPManualConstants.NOTE_TAG_ERROR, 'errors', 'error', header=header)
    update_refs_('tasks', html, li.id2filename, li.main_headers)
    write_data_to_file(str(html), fn, quiet=True)
    if nerrors:
        manifest.append(dict(display='%d errors' % nerrors,
                             filename='errors.html'))

        msg = 'I am sorry to say that there were %d errors.\n\nPlease see: %s' % (nerrors, fn)
        logger.error('\n\n\n' + indent(msg, ' ' * 15) + '\n\n')

    fn = os.path.join(d, 'errors_and_warnings.manifest.yaml')
    write_data_to_file(yaml.dump(manifest), fn, quiet=False)

    fn = os.path.join(d, 'errors_and_warnings.pickle')
    res = AugmentedResult()
    res.merge(aug)
    write_data_to_file(pickle.dumps(res), fn, quiet=False)


def write_manifest_html(d):
    manifest = [dict(display='html', filename='index.html')]
    fn = os.path.join(d, 'output-html.manifest.yaml')
    write_data_to_file(yaml.dump(manifest), fn, quiet=False)


def write_manifest_pdf(out_pdf):
    d = os.path.dirname(out_pdf)
    basename = os.path.basename(out_pdf)
    manifest = [dict(display='PDF', filename=basename)]
    fn = os.path.join(d, 'output-pdf.manifest.yaml')
    write_data_to_file(yaml.dump(manifest), fn, quiet=False)


def is_ignored_by_catkin(dn):
    """ Returns true if the directory is inside one with CATKIN_IGNORE """
    while dn != '/':
        i = os.path.join(dn, "CATKIN_IGNORE")
        if os.path.exists(i):
            return True
        dn = os.path.dirname(dn)
        if not dn:
            return False
    return False


from mcdp_docs.location import LocationInString


def job_bib_contents(context, bib_files):
    bib_files = natsorted(bib_files)
    # read all contents
    contents = ""
    for fn in bib_files:
        contents += read_data_from_file(fn) + '\n\n'
    h = get_md5(contents)[:8]
    job_id = 'bibliography-' + h
    return context.comp(run_bibtex2html, contents, job_id=job_id)


def get_main_template(root_dir, resources_dirs):
    fn = os.path.join(root_dir, MCDPManualConstants.main_template)
    if os.path.exists(fn):
        return parse_main_template(fn)

    for d in resources_dirs:
        fns = locate_files(d, MCDPManualConstants.main_template)
        for fn in fns:
            return parse_main_template(fn)

    msg = 'Could not find template {}'.format(fn)
    raise ValueError(msg)


def parse_main_template(fn):
    template = open(fn).read()

    soup = bs_entire_document(template)
    base_dir = os.path.dirname(fn)
    embed_css_files(soup, base_dir)

    head = soup.find('head')
    if head is None:
        msg = 'Could not find <head> in template'
        logger.error(msg)
        logger.error(str(soup))
        raise Exception(msg)

    template = to_html_entire_document(soup)
    return template


def write(s_aug, out):
    s = s_aug.get_result()
    write_data_to_file(s, out)


def render_book(src_dirs, generate_pdf,
                data, realpath,
                use_mathjax,
                raise_errors,
                filter_soup=None,
                symbols=None,
                ignore_ref_errors=False,
                ):
    """ Returns an AugmentedResult(str) """
    res = AugmentedResult()
    from mcdp_docs.pipeline import render_complete

    librarian = get_test_librarian()
    # XXX: these might need to be changed
    if not MCDPConstants.softy_mode:
        for src_dir in src_dirs:
            librarian.find_libraries(src_dir)

    load_library_hooks = [librarian.load_library]
    library_ = MCDPLibrary(load_library_hooks=load_library_hooks)

    for src_dir in src_dirs:
        library_.add_search_dir(src_dir)

    d = tempfile.mkdtemp()
    library_.use_cache_dir(d)

    location = LocalFile(realpath)

    # print('location:\n%s' % location)

    def filter_soup0(soup, library):
        if filter_soup is not None:
            filter_soup(soup=soup, library=library)
        add_edit_links2(soup, location)
        add_last_modified_info(soup, location)

    try:
        html_contents = render_complete(library=library_,
                                        s=data,
                                        raise_errors=raise_errors,
                                        realpath=realpath,
                                        use_mathjax=use_mathjax,
                                        symbols=symbols,
                                        generate_pdf=generate_pdf,
                                        filter_soup=filter_soup0,
                                        location=location,
                                        res=res,
                                        ignore_ref_errors=ignore_ref_errors)
    except DPSyntaxError as e:
        msg = 'Could not compile %s' % realpath
        location0 = LocationInString(e.where, location)
        res.note_error(msg, locations=location0)
        fail = "<p>This file could not be compiled</p>"
        res.set_result(fail)
        return res
        # raise_wrapped(DPSyntaxError, e, msg, compact=True)

    if False:  # write minimal doc
        doc = get_minimal_document(html_contents,
                                   add_markdown_css=True, extra_css=extra_css)
        dirname = main_file + '.parts'
        if dirname and not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except:
                pass
        fn = os.path.join(dirname, '%s.html' % out_part_basename)
        write_data_to_file(doc, fn)

    res.set_result(html_contents)
    return res


mcdp_render_manual_main = RenderManual.get_sys_main()
