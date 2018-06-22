import pickle
import shutil
import sys
from collections import OrderedDict

import yaml
from bs4 import Tag
from junit_xml import TestSuite, TestCase

from mcdp_docs import logger
from mcdp_docs.embed_css import embed_css_files
from mcdp_docs.manual_constants import MCDPManualConstants
from mcdp_docs.mcdp_render_manual import get_extra_content, CROSSREF_CSS, CROSSREF_SCRIPT
from mcdp_docs.sync_from_circle import get_artefacts, get_links2, locate_files
from mcdp_report.html import get_css_filename
from mcdp_utils_misc import write_data_to_file, AugmentedResult
from mcdp_utils_xml import bs, gettext, bs_entire_document, to_html_entire_document

BOOKS = """
!!omap
- base:
    title: Information about the project

    abstract: |
        This is general information about the project
        and how to contribute to it.

    books: !!omap

        - the_duckietown_project:
            title: The Duckietown Project
            abstract: |
                Learn about the history and current status.

        - AI_driving_olympics:
            title: The AI Driving Olympics
            abstract: |
                Learn about the 2018 competition at NIPS.

        - guide_for_instructors:
            title: Guide for instructors

        - duckumentation:
            title: Contributing to the documentation


- tech:
    title: Operation manuals

    abstract: |

        These are the operation manuals.

    books: !!omap

        - opmanual_duckiebot:
            title: Duckiebot manual

        - opmanual_duckietown:
            title: Duckietown manual

        - software_carpentry:
            title: Reference for useful commands

- SW:
    title: Software development

    books: !!omap
        - software_architecture:
            title: Duckietown software architecture

        - software_devel:
            title: Software development in Duckietown

        - code_docs:
            title: Packages documentation


- theory:
    title: Class materials

    books: !!omap

        - learning_materials:
            title: Learning materials

        - exercises:
            title: Exercises

        - preliminaries:
            title: Preliminaries


- fall2017:
    title: Past editions
    books: !!omap

        - class_fall2017:
            title: Fall 2017

        - class_fall2017_projects:
            title: Fall 2017 projects

- misc:
    title: Miscellanea

    abstract: |
        Other content

    books: !!omap
        - drafts:
            title: Drafts

        - deprecated:
            title: Deprecated

"""


def go():
    groups = OrderedDict(yaml.load(BOOKS))

    import os

    dist = 'duckuments-dist'

    html = Tag(name='html')
    head = Tag(name='head')
    meta = Tag(name='meta')
    meta.attrs['content'] = "text/html; charset=utf-8"
    meta.attrs['http-equiv'] = "Content-Type"

    stylesheet = 'v_manual_split'
    link = Tag(name='link')
    link['rel'] = 'stylesheet'
    link['type'] = 'text/css'
    link['href'] = get_css_filename('compiled/%s' % stylesheet)
    head.append(link)

    body = Tag(name='body')

    style = Tag(name='style')

    style.append(CSS)

    head.append(style)
    head.append(meta)

    html.append(head)
    html.append(body)

    divgroups = Tag(name='div')
    all_crossrefs = Tag(name='div')

    res = AugmentedResult()

    for id_group, group in groups.items():
        divgroup = Tag(name='div')
        divgroup.attrs['class'] = 'group'
        divgroup.attrs['id'] = id_group

        h0 = Tag(name='h1')
        h0.append(group['title'])

        divgroup.append(h0)

        if 'abstract' in group:
            p = Tag(name='p')
            p.append(group['abstract'])
            divgroup.append(p)

        books = group['books']
        # divbook = Tag(name='div')
        books = OrderedDict(books)
        for id_book, book in books.items():
            d = os.path.join(dist, id_book)
            change_frame(d, '../../', current_slug=id_book)

            d0 = dist

            errors_and_warnings = os.path.join(d, 'out', 'errors_and_warnings.pickle')
            if os.path.exists(errors_and_warnings):
                resi = pickle.loads(open(errors_and_warnings).read())
                # print(errors_and_warnings)

                resi.update_file_path(prefix=os.path.join(id_book, 'out'))
                res.merge(resi)
            else:
                msg = 'Path does not exist: %s' % errors_and_warnings
                logger.error(msg)

            artefacts = get_artefacts(d0, d)

            div = Tag(name='div')
            div.attrs['class'] = 'book-div'
            div.attrs['id'] = id_book
            div_inside = Tag(name='div')
            div_inside.attrs['class'] = 'div_inside'
            links = get_links2(artefacts)

            for a in links.select('a'):
                s = gettext(a)
                if 'error' in s or 'warning' in s or 'task' in s:
                    a['class'] = 'EWT'

            if False:
                h = Tag(name='h3')
                h.append(book['title'])

                # div_inside.append(h)
                if 'abstract' in book:
                    p = Tag(name='p')
                    p.append(book['abstract'])
                    div_inside.append(p)

            div_inside.append(links)
            div.append(div_inside)

            toc = os.path.join(d, 'out/toc.html')
            if os.path.exists(toc):
                data = open(toc).read()
                x = bs(data)
                for a in x.select('a[href]'):
                    href = a.attrs['href']
                    a.attrs['href'] = id_book + '/out/' + href
                x.name = 'div'  # not fragment
                div.append(x)
            crossrefs = os.path.join(d, 'crossref.html')
            if os.path.exists(crossrefs):
                x = bs(open(crossrefs).read())
                for e in x.select('[url]'):
                    all_crossrefs.append('\n\n')
                    all_crossrefs.append(e.__copy__())
            else:
                logger.error('File does not exist %s' % crossrefs)

            divgroup.append(div)
        divgroups.append(divgroup)

    out_pickle = sys.argv[3]

    nwarnings = len(res.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_WARNING))
    ntasks = len(res.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_TASK))
    nerrors = len(res.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_ERROR))
    logger.info('%d tasks' % ntasks)
    logger.warning('%d warnings' % nwarnings)
    logger.error('%d nerrors' % nerrors)

    from mcdp_docs.mcdp_render_manual import write_errors_and_warnings_files
    write_errors_and_warnings_files(res, os.path.dirname(out_pickle))

    out_junit = os.path.join(os.path.dirname(out_pickle), 'junit', 'notes', 'junit.xml')
    s = get_junit_xml(res)
    write_data_to_file(s.encode('utf8'), out_junit)

    # write_data_to_file(pickle.dumps(res), out_pickle, quiet=False)

    extra = get_extra_content(res)

    extra.attrs['id'] = 'extra'
    body.append(extra)
    body.append(divgroups)

    embed_css_files(html)

    for e in body.select('.notes-panel'):
        e.extract()
    out = sys.argv[1]
    data = str(html)
    data = data.replace('<body>', '<body>\n<?php header1() ?>\n')
    write_data_to_file(data, out)

    manifest = [dict(display='index', filename=os.path.basename(out))]
    mf = os.path.join(os.path.dirname(out), 'summary.manifest.yaml')
    write_data_to_file(yaml.dump(manifest), mf)

    out_crossrefs = sys.argv[2]

    html = Tag(name='html')
    head = Tag(name='head')
    body = Tag(name='body')
    style = Tag(name='style')
    style.append(CROSSREF_CSS)
    head.append(style)
    html.append(head)

    script = Tag(name='script')
    script.append(CROSSREF_SCRIPT)

    container = Tag(name='div')
    container.attrs['id'] = 'container'
    body.append(container)

    details = Tag(name='details')
    summary = Tag(name='summary')
    summary.append('See all references')
    details.append(summary)
    details.append(all_crossrefs)
    body.append(details)
    body.append(script)
    html.append(body)

    write_data_to_file(str(html), out_crossrefs)

    if nerrors > 0:
        sys.exit(nerrors)


def get_junit_xml(res):
    # notes = res.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_WARNING)
    notes = res.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_ERROR)

    test_cases = []
    for i, note in enumerate(notes):
        tc = junit_test_case_from_note(i, note)
        test_cases.append(tc)

    ts = TestSuite("notes", test_cases)

    return TestSuite.to_xml_string([ts])


def flatten_ascii(s):
    if s is None:
        return None
    s = unicode(s, encoding='utf8', errors='replace')
    s = s.encode('ascii', errors='ignore')
    return s


def junit_test_case_from_note(i, note):
    # stderr = str(note)
    # stdout = ''
    tc = TestCase(name='note%03d' % i)

    # if cache.state == Cache.FAILED:
    #     message = cache.exception
    #     output = cache.exception + "\n" + cache.backtrace
    output = ''
    ns = flatten_ascii(str(note))
    ns = ns.replace('\n', '\a')
    tc.add_failure_info(ns, flatten_ascii(output))
    return tc


import os


def change_frame(d0, rel, current_slug):
    for f in locate_files(d0, '*.html'):
        basename = os.path.basename(f)
        if basename in ['out.html', 'toc.html']:
            continue
        if 'revealjs' in basename:
            continue
        print(f)
        do_it(f, rel, current_slug)


def do_it(f, rel, current_slug):
    f2 = f + '.old'
    if not os.path.exists(f2):
        shutil.copy(f, f2)
    orig = open(f2).read()

    soup = bs_entire_document(orig)
    soup2 = make_changes(soup, f, rel, current_slug)
    data = to_html_entire_document(soup2)

    data = data.replace('<body>', '<body>\n<?php header1() ?>\n')
    write_data_to_file(data, f, quiet=True)


def make_changes(soup, f, rel, current_slug):
    s = bs(SPAN_BOOKS)

    for option in s.select('option[value]'):
        # noinspection PyAugmentAssignment
        option.attrs['value'] = rel + option.attrs['value']

        if current_slug in option.attrs['value']:
            option.attrs['selected'] = 1

    for a in s.select('a[href]'):
        # noinspection PyAugmentAssignment
        a.attrs['href'] = rel + a.attrs['href']

    tocdiv = soup.select_one('#tocdiv')
    if tocdiv is not None:
        tocdiv.insert(0, s)

    return soup


# language=html
SPAN_BOOKS = '''

<script>

function changed(e) {
    loc = e.value;
    window.location = loc;
}

</script>
<style>
#books {
    margin-bottom:2em;
}
</style>
            <div id="books">
            <a target='frame' href="index.html">Home</a>

        <select onchange="changed(this)">
    <option
            value="summary.html">Summary</option>
    <option
            value="the_duckietown_project/out/index.html">The Duckietown Project</option>
    <option
            value="guide_for_instructors/out/index.html">Guide for instructors</option>

    <option
            value="duckumentation/out/index.html">Contributing to the documentation</option>

    <option id="opmanual_duckiebot"
            value="opmanual_duckiebot/out/index.html">Duckiebot operation manual </option>
    <option id="opmanual_duckietown" onclick="activate(this)" value="opmanual_duckietown/out/index.html">Duckietown operation manual</option>
    <option id="software_carpentry" onclick="activate(this)" value="software_carpentry/out/index.html">Software carpentry</option>

    <option target='frame' id="software_architecture" onclick="activate(this)"
            value="software_architecture/out/index.html">SW Architecture</option>
    <option target='frame' id="software_devel" onclick="activate(this)"
            value="software_devel/out/index.html">SW Development</option>

    <option target='frame' id="learning_materials" onclick="activate(this)" value="learning_materials/out/index.html">Learning materials</option>

    <option target='frame' id="exercises" onclick="activate(this)" value="exercises/out/index.html">Exercises</option>
    <option target='frame' id="preliminaries" onclick="activate(this)" value="preliminaries/out/index.html">Preliminaries</option>

    <option target='frame' id="class_fall2017" onclick="activate(this)" value="class_fall2017/out/index.html">Fall 2017
        class</option>
    <option target='frame' id="class_fall2017_projects" onclick="activate(this)"
            value="class_fall2017_projects/out/index.html">Fall 2017 projects</option>

    <option target='frame' id="deprecated" onclick="activate(this)" value="deprecated/out/index.html">Deprecated material</option>
    <option target='frame' id="drafts" onclick="activate(this)" value="drafts/out/index.html">Drafts</option>
<!--<option value="http://docs.duckietown.org/duckuments.html">Builds</option>-->

    </select>
    </div>
    
    <script>
        (function (i, s, o, g, r, a, m) {
            i['GoogleAnalyticsObject'] = r;
            i[r] = i[r] || function () {
                (i[r].q = i[r].q || []).push(arguments)
            }, i[r].l = 1 * new Date();
            a = s.createElement(o),
                m = s.getElementsByTagName(o)[0];
            a.async = 1;
            a.src = g;
            m.parentNode.insertBefore(a, m)
        })(window, document, 'script', 'https://www.google-analytics.com/analytics.js', 'ga');
        ga('create', 'UA-119606699-2', 'auto');
        ga('send', 'pageview');
    </script>

'''
# language=css
CSS = """
    body {
        width: 100% !important;
        margin: 1em !important;
        padding: 0 !important;

    }
    .EWT {
        display: none;
        font-weight: bold;
        font-size: smaller;
        color: darkblue;
    }
    a.EWT {
        text-decoration: none;
        font-family: arial;
    }
    .show_todos .EWT {
        display: inline;
    }
    .toc_what {
        display: none;
    }

    .toc_a_for_part {
        padding-top: 0;

    }

    .toc_a_for_book {
        font-size: 150%;
        font-weight: bold;
        margin-top: 0.2em;
    }
    .toc_a_for_book::after {
        font-size: 100%;
    }

    h3 {
        font-size: 150%;
        color: black;
        text-align: left;
        border-bottom: 0;
        margin-top: 0.3em;
        padding-top: 0;
    }

    div.group {
        column-count: auto;
        column-width: 22em;
        width: calc(100% - 4em);
        display: block;
        background-color: #eaeaea;
        padding: 1em;
        margin: 1em;
        min-height: 12em;
    }

    div.book-div span a:nth-child(2) {
        margin-right: 2em;
    }
    div.book-div {
        background-color: #ddd;
        margin: 1em;
        padding: 10px;
    }
    .div_inside {
        break-inside: avoid;
    }
    ul,li {
    list-style: none;
    }
    #extra .notes-panel {
    /* display: none;*/
    }
    #extra p {
    max-width: 100%;
    }
    .toc_ul-depth-3 {
    display: none;
    }
    """

if __name__ == '__main__':
    go()
