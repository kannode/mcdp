# -*- coding: utf-8 -*-
import getpass
import logging
import os
from contextlib import contextmanager
from multiprocessing import cpu_count

from bs4.element import Tag
from contracts import contract
from mcdp import logger
from mcdp_docs.check_missing_links import get_id2element
from mcdp_docs.embed_css import embed_css_files
from mcdp_docs.manual_constants import MCDPManualConstants

from mcdp_docs.tocs import generate_toc, substituting_empty_links
from mcdp_utils_misc import get_md5, write_data_to_file
from mcdp_utils_misc.augmented_result import AugmentedResult
from mcdp_utils_misc.timing import timeit_wall
from mcdp_utils_xml import read_html_doc_from_file, to_html_entire_document
from mcdp_utils_xml.parsing import bs, bs_entire_document
from mcdp_utils_xml.project_text import gettext
from quickapp import QuickApp

from .add_mathjax import add_mathjax_call, add_mathjax_preamble
from .extract_assets import extract_assets_from_file, save_css
from .manual_join_imp import (add_prev_next_links, split_in_files, get_id2filename,
                              create_link_base, create_link_base_js, update_refs_)
from .source_info_imp import get_first_header_title

show_timing = False

if getpass.getuser() == 'andrea':
    show_timing = False
    pass
#    show_timing = False

if show_timing:
    timeit = timeit_wall
else:

    @contextmanager
    def timeit(_s):
        yield


def make_page(contents, head0, add_toc, extra_panel_content, add_home_link):
    """ Returns html (Beautiful Soup document) """
    html = Tag(name='html')

    head = head0.__copy__()
    html.append(head)
    body = Tag(name='body')

    with timeit('make_page() / copy toc'):
        if add_toc is not None:
            tocdiv = Tag(name='div')
            tocdiv.attrs['id'] = 'tocdiv'
            if add_home_link:
                a = Tag(name='a')
                a.append('Home')
                a.attrs['href'] = 'index.html'
                p = Tag(name='p')
                p.append(a)
                tocdiv.append(p)

            if extra_panel_content is not None:
                details = Tag(name='details')
                summary = Tag(name='summary')
                summary.append('build details')
                details.append(summary)
                details.append(extra_panel_content)
                tocdiv.append(details)

            tocdiv.append(add_toc)

            body.append(tocdiv)

    section_name = get_first_header_title(contents)
    if section_name is not None:
        section_name = section_name.replace('</code>', '</code> ')
        section_name = gettext(bs(section_name))
        title2 = Tag(name='title')
        title2.append(section_name)

        title = head.find('title')
        if title is None:
            head.append(title2)
        else:
            title.replace_with(title2)

    not_toc = Tag(name='div')
    not_toc.attrs['id'] = 'not-toc'
    not_toc.append(contents)
    body.append(not_toc)
    html.append(body)

    # delete the original one
    if False:
        main_toc = contents.find(id=MCDPManualConstants.MAIN_TOC_ID)
        if main_toc is not None:
            main_toc.extract()

    return html


def only_second_part(mathjax, preamble, html, id2filename, filename):
    if mathjax:
        if preamble is not None:
            with timeit('add_mathjax_preamble()'):
                add_mathjax_preamble(html, preamble)

        with timeit('add_mathjax_call'):
            add_mathjax_call(html)

    with timeit('update_refs_'):
        update_refs_(filename, html, id2filename)

    with timeit('serialize'):
        result = str(html)

    return result


class Split(QuickApp):
    """ Splits the manual into files """

    def define_options(self, params):
        params.add_string('filename', help="""Input filename""")
        params.add_string('output_dir', help='Output directory')
        params.add_flag('disqus')  # ignored
        params.add_flag('mathjax')
        params.add_string('preamble', default=None)
        params.add_flag('faster_but_imprecise')  # ignored
        params.add_int("workers", default=0)

    def define_jobs_context(self, context):
        ifilename = self.options.filename
        output_dir = self.options.output_dir
        mathjax = self.options.mathjax
        preamble = self.options.preamble
        nworkers = self.options.workers
        logger.setLevel(logging.DEBUG)

        self.debug("Using n = %d workers" % nworkers)

        data = open(ifilename).read()
        data_aug = AugmentedResult()
        data_aug.set_result(data)
        create_split_jobs(context, data_aug, mathjax, preamble, output_dir, nworkers=nworkers)


def create_split_jobs(context, data_aug, mathjax, preamble, output_dir, nworkers=0,
                      extra_panel_content=None,
                      add_toc_if_not_existing=True,
                      output_crossref=None,
                      permalink_prefix=None,
                      only_refs=False):
    data = data_aug.get_result()
    if nworkers == 0:
        nworkers = max(1, cpu_count() - 2)

    res = AugmentedResult()
    res.merge(data_aug)

    h = get_md5(data)[-4:]
    jobs = []

    assets_dir = os.path.join(output_dir, 'assets')

    with timeit("preprocess"):
        soup = bs_entire_document(data)
        embed_css_files(soup)
        fo = os.path.join(output_dir, 'dummy.html')
        save_css(soup, fo, assets_dir)
        data = to_html_entire_document(soup)

    for i in range(nworkers):
        promise = context.comp_dynamic(go, i, nworkers, data, mathjax, preamble, output_dir,
                                       add_toc_if_not_existing=add_toc_if_not_existing,
                                       assets_dir=assets_dir,
                                       extra_panel_content=extra_panel_content,
                                       output_crossref=output_crossref,
                                       permalink_prefix=permalink_prefix,
                                       only_refs=only_refs,
                                       job_id='worker-%d-of-%d-%s' % (i, nworkers, h))
        jobs.append(promise)
        if only_refs:
                break

    return context.comp(notification, res, jobs, output_dir)


def notification(aug, jobs_aug, output_dir):
    res = AugmentedResult()
    res.merge(aug)
    for job_aug in jobs_aug:
        res.merge(job_aug)
        res.set_result(job_aug.get_result())
    main = os.path.join(output_dir, 'index.html')
    msg = '\n \n      The HTML version is ready at %s ' % main
    msg += '\n \n \nPlease wait a few more seconds for the PDF version.'
    logger.info(msg)
    return res


@contract(returns=AugmentedResult)
def go(context, worker_i, num_workers, data, mathjax, preamble, output_dir, assets_dir,
       add_toc_if_not_existing, extra_panel_content, permalink_prefix=None, output_crossref=None,
       only_refs=False):
    res = AugmentedResult()
    soup = bs_entire_document(data)

    # extract the main toc if it is there
    with timeit("Extracting main toc"):
        main_toc = soup.find(id=MCDPManualConstants.MAIN_TOC_ID)

        if main_toc is None:

            if add_toc_if_not_existing:
                # logger.info('Generating TOC because it is not there')

                main_toc = bs(generate_toc(soup)).ul
                main_toc.attrs['class'] = 'toc'  # XXX: see XXX13
                assert main_toc is not None
                substituting_empty_links(main_toc, raise_errors=False, res=res,
                                         extra_refs=soup)

            else:
                msg = 'Could not find main toc (id #%s)' % MCDPManualConstants.MAIN_TOC_ID
                res.note_error(msg)
                main_toc = Tag(name='div')
                main_toc.append('TOC NOT FOUND')
        else:
            main_toc = main_toc.__copy__()

        if 'id' in main_toc.attrs:
            del main_toc.attrs['id']

    # XXX: this is not the place to do it
    mark_toc_links_as_errored(main_toc, soup)


    body = soup.html.body

    with timeit("split_in_files"):
        filename2contents = split_in_files(body)
        id2filename = get_id2filename(filename2contents)

    res.set_result(id2filename)

    if output_crossref is not None:
        from mcdp_docs.mcdp_render_manual import write_crossref_info
        context.comp(write_crossref_info, data=data, id2filename=id2filename,
                     output_crossref=output_crossref,
                     permalink_prefix=permalink_prefix)

    if only_refs:
        logger.debug('Skipping rest because only_refs')
        return res

    with timeit("add_prev_next_links"):
        filename2contents = add_prev_next_links(filename2contents)

    with timeit("preparing assets dir"):
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except:
                pass

    with timeit("creating link.html and link.js"):

        linkbase = 'link.html'  # do not change (it's used by http://purl.org/dth)
        linkbasejs = 'link.js'

        lb = create_link_base(id2filename)
        write_data_to_file(str(lb), os.path.join(output_dir, linkbase), quiet=True)

        linkjs = create_link_base_js(id2filename)
        write_data_to_file(str(linkjs), os.path.join(output_dir, linkbasejs), quiet=True)



    if preamble is not None:
        if preamble.endswith('.tex'):  # XXX
            preamble = open(preamble).read()

    ids_to_use = []
    for k in list(id2filename):
        if not 'autoid' in k:
            ids_to_use.append(k)
    ids_to_use = sorted(ids_to_use)

    pointed_to = []
    for k in ids_to_use:
        f = id2filename[k]
        if not f in pointed_to:
            pointed_to.append(f)

    # data = ",".join(pointed_to)
    head0 = soup.html.head

    if True:
        context.comp(remove_spurious, output_dir, list(filename2contents))

    with timeit('main_toc copy'):
        main_toc0 = main_toc.__copy__()

        main_toc0_s = str(main_toc0)
    asset_jobs = []
    for i, (filename, contents) in enumerate(filename2contents.items()):
        if i % num_workers != worker_i:
            continue
        with timeit('main_toc copy hack'):
            main_toc = bs(main_toc0_s).ul
            assert main_toc is not None

        # Trick: we add the main_toc, and then ... (look below)
        with timeit('make_page'):
            add_home_link = 'index.html' not in filename2contents
            html = make_page(contents, head0, main_toc, extra_panel_content, add_home_link=add_home_link)

        with timeit("direct job"):
            result = only_second_part(
                    mathjax, preamble, html, id2filename, filename)

            # ... we remove it. In this way we don't have to copy it every time...
            main_toc.extract()

            fn = os.path.join(output_dir, filename)


            h = get_md5(result)[:8]
            r = context.comp(extract_assets_from_file, result, fn, assets_dir,
                             job_id='%s-%s-assets' % (filename, h))
            asset_jobs.append(r)

    update_refs_('toc.html', main_toc, id2filename)
    out_toc = os.path.join(output_dir, 'toc.html')
    write_data_to_file(str(main_toc), out_toc, quiet=True)

    return context.comp(wait_assets, res, asset_jobs)


def mark_toc_links_as_errored(main_toc, soup):
    id2element, duplicates = get_id2element(soup, 'id')

    for a in main_toc.select('a.toc_link'):
        _id = a['href'][1:]
        if _id in id2element:
            element = id2element[_id]
            section = element.parent

            for attname in MCDPManualConstants.attrs_to_copy_to_link:
                if attname in section.attrs:
                    a.attrs[attname] = section.attrs[attname]

            # compute last modified
            min_ = min0 = 100000
            author = '?'
            for x in section.select('[%s]' % MCDPManualConstants.ATTR_GITHUB_LAST_MODIFIED_DAYS):
                n = x.attrs[MCDPManualConstants.ATTR_GITHUB_LAST_MODIFIED_DAYS]
                n = int(n)

                min_ = min(n, min_)
                if min_ == n:
                    if MCDPManualConstants.ATTR_GITHUB_LAST_MODIFIED_AUTHOR in x.attrs:
                        author = x.attrs[MCDPManualConstants.ATTR_GITHUB_LAST_MODIFIED_AUTHOR]

            if min_ != min0:
                element.attrs[MCDPManualConstants.ATTR_GITHUB_LAST_MODIFIED_DAYS] = \
                section.attrs[MCDPManualConstants.ATTR_GITHUB_LAST_MODIFIED_DAYS] = \
                a.attrs[MCDPManualConstants.ATTR_GITHUB_LAST_MODIFIED_DAYS] = str(min_)

                a.attrs[MCDPManualConstants.ATTR_GITHUB_LAST_MODIFIED_AUTHOR] = author

            ndrafts = len(list(section.select('[%s=draft]' % MCDPManualConstants.ATTR_STATUS)))
            # print('%d contained' % ndrafts)
            if ndrafts:
                a[MCDPManualConstants.ATTR_STATUS] = 'draft'

            nchanges = len(list(section.select('[%s]'%MCDPManualConstants.ATTR_HAS_LOCAL_MODIFICATIONS)))
            if nchanges:
                a[MCDPManualConstants.ATTR_HAS_LOCAL_MODIFICATIONS] = '%d' % nchanges


            nerrors = 0
            ntasks = 0
            nwarnings = 0
            for d in section.select('details'):
                classes = d.attrs['class']
                if 'error' in classes:
                    nerrors += 1
                if 'task' in classes:
                    ntasks += 1
                if 'warning' in classes:
                    nwarnings += 1

            summary = []
            if nerrors:
                summary.append('%d errors' % nerrors)
                a.attrs['nerrors'] = str(nerrors)
            if nwarnings:
                summary.append('%d warnings' % nwarnings)
                a.attrs['nwarnings'] = str(nwarnings)
            if ntasks:
                summary.append('%d tasks' % ntasks)
                a.attrs['ntasks'] = str(ntasks)
            if summary:
                a.attrs['summary'] = " ".join(summary)

            # print 'found %s %s %s' % (section.name, summary, section.attrs)


def wait_assets(res, asset_jobs):
    for a in asset_jobs:
        res.merge(a)
    return res


def identity(x):
    return x


split_main = Split.get_sys_main()


def remove_spurious(output_dir, filenames):
    ignore = ['link.html', 'toc.html', 'errors.html', 'warnings.html', 'tasks.html', 'crossref.html']
    found = os.listdir(output_dir)
    for f in found:
        if not f.endswith('.html'):
            continue
        if f in ignore:
            continue
        if f not in filenames:
            fn = os.path.join(output_dir, f)

            if 'SPURIOUS' in open(fn).read():
                # already marked as spurious
                continue

            msg = 'I found a spurious file from earlier compilations: %s' % fn
            #             msg += '(%s not in %s) ' % (f, filenames)
            logger.warning(msg)

            soup = read_html_doc_from_file(fn)
            e = soup.find('section')
            if e is not None and 'id' in e.attrs:
                if False:
                    id_ = e.attrs['id'].replace(':section', '')
                    if 'autoid' not in id_:
                        id_ = remove_prefix(id_)
                        url = 'http://purl.org/dt/master/' + id_
                        OTHER = (('<p>Maybe try this link to find the version on master '
                                  '(no guarantees): <a href="%s">%s</a></p>') % (url, url))
                        OTHER += '\n<p>If that does not work, the section was renamed.</p>'
                    else:
                        OTHER = ''
                else:
                    OTHER = ''
            else:
                OTHER = ''

            data = spurious.replace('OTHER', OTHER)
            write_data_to_file(data, fn, quiet=True)


# language=html
spurious = """
<html>
<head><title>Spurious file</title></head>
<body> <!-- SPURIOUS -->

<h2>Spurious file</h2>
<p>This file is a spurious remain from earlier compilation.</p>

<p>If you are reached this file, it means that somebody is not using PURLs
to link to parts of the materials.</p>

OTHER

</body>
</html>
"""
