from contextlib import contextmanager
from multiprocessing import cpu_count
import getpass
import logging
import os

from bs4.element import Tag

from mcdp import logger
from mcdp_docs.embed_css import embed_css_files
from mcdp_utils_misc import get_md5, write_data_to_file, create_tmpdir
from mcdp_utils_misc.timing import timeit_wall
from mcdp_utils_xml import read_html_doc_from_file
from mcdp_utils_xml.parsing import bs, bs_entire_document
from mcdp_utils_xml.project_text import gettext
from quickapp import QuickApp

from .add_mathjax import add_mathjax_call, add_mathjax_preamble
from .extract_assets import extract_assets_from_file
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


def make_page(contents, head0, add_toc):
    """ Returns html (Beautiful Soup document) """
    html = Tag(name='html')

    head = head0.__copy__()
    html.append(head)
    body = Tag(name='body')

    with timeit('make_page() / copy toc'):
        if add_toc is not None:
            tocdiv = Tag(name='div')
            tocdiv.attrs['id'] = 'tocdiv'
            tocdiv.append(add_toc)

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

    body.append(tocdiv)
    not_toc = Tag(name='div')
    not_toc.attrs['id'] = 'not-toc'
    not_toc.append(contents)
    body.append(not_toc)
    html.append(body)

    # delete the original one
    if False:
        main_toc = contents.find(id='main_toc')
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
        create_split_jobs(context, data, mathjax, preamble, output_dir, nworkers=nworkers)


def create_split_jobs(context, data, mathjax, preamble, output_dir, nworkers=0):
    if nworkers == 0:
        nworkers = max(1, cpu_count() - 2)

    h = get_md5(data)[-4:]
    jobs = []
    for i in range(nworkers):
        promise = context.comp_dynamic(go, i, nworkers, data, mathjax, preamble, output_dir,
                                       job_id='worker-%d-of-%d-%s' % (i, nworkers, h))
        jobs.append(promise)

    return context.comp(notification, jobs, output_dir)


def notification(_jobs, output_dir):
    main = os.path.join(output_dir, 'index.html')
    msg = '\n \n      *** The HTML version is ready at %s *** ' % main
    msg += '\n \n \nPlease wait a few more seconds for the PDF version.'
    logger.info(msg)


def go(context, worker_i, num_workers, data, mathjax, preamble, output_dir):
    with timeit("parsing"):
        soup = bs_entire_document(data)
        embed_css_files(soup)

    # extract the main toc if it is there

    with timeit("Extracting main_toc"):
        main_toc = soup.find(id='main_toc')

        if main_toc is None:
            msg = 'Could not find the element #main_toc.'
            raise ValueError(msg)

        main_toc = main_toc.__copy__()
        del main_toc.attrs['id']

    body = soup.html.body

    with timeit("split_in_files"):
        filename2contents = split_in_files(body)

    with timeit("add_prev_next_links"):
        filename2contents = add_prev_next_links(filename2contents)

    with timeit("preparing assets dir"):
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except:
                pass

        assets_dir = os.path.join(output_dir, 'assets')

    with timeit("creating link.html and link.js"):
        id2filename = get_id2filename(filename2contents)

        linkbase = 'link.html'  # do not change (it's used by http://purl.org/dth)
        linkbasejs = 'link.js'

        lb = create_link_base(id2filename)
        write_data_to_file(str(lb), os.path.join(output_dir, linkbase), quiet=True)

        linkjs = create_link_base_js(id2filename)
        write_data_to_file(str(linkjs), os.path.join(output_dir, linkbasejs), quiet=True)

    if preamble:
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

    data = ",".join(pointed_to)
#    links_hash = get_md5(data)[:8]
#     if self.options.faster_but_imprecise:
#         links_hash = "nohash"
#
#     logger.debug('hash data: %r' % data)
#    logger.debug('hash value: %r' % links_hash)

    head0 = soup.html.head

    if True:
        context.comp(remove_spurious, output_dir, list(filename2contents))

    tmpd = create_tmpdir()

#    n = len(filename2contents)
    with timeit('main_toc copy'):
        main_toc0 = main_toc.__copy__()

        main_toc0_s = str(main_toc0)
        with open('toc0.html', 'w') as f:
            f.write(main_toc0_s)
#        main_toc0_pickle = pickle.dumps(main_toc)

    asset_jobs = []
    for i, (filename, contents) in enumerate(filename2contents.items()):
        if (i % num_workers != worker_i):
            continue

#        with timeit('main_toc copy'):
#            main_toc = main_toc0.__copy__()
        with timeit('main_toc copy hack'):
            main_toc = bs(main_toc0_s)
#        with timeit('main_toc copy pickle'):
#            main_toc = cPickle.loads(main_toc0_pickle)

        # Trick: we add the main_toc, and then ... (look below)
        with timeit('make_page'):
            html = make_page(contents, head0, main_toc)

#        logger.debug('%d/%d: %s' % (i, n, filename))
        with timeit("direct job"):
            result = only_second_part(
                         mathjax, preamble, html, id2filename, filename)

            # ... we remove it. In this way we don't have to copy it every time...
            main_toc.extract()

            fn = os.path.join(output_dir, filename)

            fn0 = os.path.join(tmpd, filename)
            write_data_to_file(result, fn0, quiet=True)

            h = get_md5(result)[:8]
            r = context.comp(extract_assets_from_file, fn0, fn, assets_dir,
                         job_id='assets-%s' % h)
            asset_jobs.append(r)
    return context.comp(wait_assets, asset_jobs)


def wait_assets(asset_jobs):
    # Wait that they are done
    pass


#def quick_copy(main_toc):
#    return bs(str(main_toc))
def identity(x):
    return x


split_main = Split.get_sys_main()


def remove_spurious(output_dir, filenames):
    ignore = ['link.html']
    found = os.listdir(output_dir)
    for f in found:
        if not f.endswith('.html'): continue
        if f in ignore: continue
        if not f in filenames:
            fn = os.path.join(output_dir, f)
            msg = 'I found a spurious file from earlier compilations: %s' % fn
#             msg += '(%s not in %s) ' % (f, filenames)
            logger.warning(msg)

            if 'SPURIOUS' in open(fn).read():
                # already marked as spurious
                continue

            soup = read_html_doc_from_file(fn)
            e = soup.find('section')
            if e is not None and 'id' in e.attrs:
                id_ = e.attrs['id'].replace(':section', '')
                from mcdp_docs.composing.cli import remove_prefix

                if not 'autoid' in id_:
                    id_ = remove_prefix(id_)
                    url = 'http://purl.org/dt/master/' + id_
                    OTHER = '<p>Maybe try this link to find the version on master (no guarantees): <a href="%s">%s</a></p>' % (url, url)
                    OTHER += '\n<p>If that does not work, the section was renamed.</p>'
                else:
                    OTHER = ''
            else:
                OTHER = ''

            data = spurious.replace('OTHER', OTHER)
            write_data_to_file(data, fn, quiet=True)


spurious = """
<html>
<head><title>Spurious file</title></head>
<body> <!-- SPURIOUS -->

<h2>Spurious file</h2>
<p>This file is a spurious remain from earlier compilation.</p>

<p>If you are reached this file, it means that somebody is not using PURLs
to link to parts of the book.</p>

OTHER

</body>
</html>
"""
