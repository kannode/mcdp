from contextlib import contextmanager
import getpass
import logging
from mcdp import logger
from mcdp_utils_misc import get_md5, write_data_to_file
from mcdp_utils_xml import bs, read_html_doc_from_file
import os
import time

from bs4.element import Tag
from quickapp import QuickApp

from .add_mathjax import add_mathjax_call, add_mathjax_preamble
from .extract_assets import extract_assets_from_file
from .manual_join_imp import add_prev_next_links, split_in_files, get_id2filename, create_link_base
from .manual_join_imp import update_refs_
from .source_info_imp import get_first_header_title
from .split_disqus import append_disqus
from mcdp_docs.manual_join_imp import create_link_base_js


show_timing = False

if getpass.getuser() == 'andrea':
    show_timing = True
    show_timing = False

@contextmanager
def timeit(s):
    t0 = time.clock()
    yield
    delta = time.clock() - t0
    if show_timing:
        logger.debug('%10d ms: %s' % ( 1000*delta, s))
    
def make_page(contents, head0, main_toc):
    """ Returns html """
    html = Tag(name='html')
    
    head = head0.__copy__()
    html.append(head)
    body = Tag(name='body')
    
    with timeit('make_page() / copy toc'):
        if main_toc:
            tocdiv = Tag(name='div')
            tocdiv.attrs['id'] = 'tocdiv' 

            toc = main_toc
            toc.extract()
            del toc.attrs['id']
            tocdiv.append(toc)

    section_name = get_first_header_title(contents)
    if section_name is not None:
        title2 = bs(section_name)
        title2.name = 'title'
        
        title = head.find('title')
        if title is None:
#             msg = 'Cannot find the "title" element'
#             msg += '\n' + indent(str(head)[:500], 'head')
#             raise Exception(msg)
            head.append(title2)
        else:
            title.replace_with(title2)
    
    body.append(tocdiv)
    not_toc = Tag(name='div')
    not_toc.attrs['id'] = 'not-toc'
    not_toc.append(contents)
    body.append(not_toc)
    html.append(body)
    return html

def split_file(ifilename, directory, filename, mathjax, preamble, disqus, id2filename, assets_dir):
#     print soup
#     print soup.html.body
    with timeit('Reading input file...'):
        soup = read_html_doc_from_file(ifilename)
    body = soup.find('body')
    if body is None:
        msg = 'Could not find body element'
        raise Exception(msg)
    head0 = soup.html.head
    # extract the main toc if it is there
    main_toc = body.find(id='main_toc')
    if main_toc is None:
        msg = 'Could not find the element #main_toc.'
        raise ValueError(msg)

    p = bs('<p><a href="index.html">Home</a></p>')
    main_toc.insert(0, p.p)
    
    assert body is not None, soup
    
    with timeit('Splitting in files...'):
        filename2contents = split_in_files(body)
    
    with timeit('add_prev_next_links()...'):
        filename2contents = add_prev_next_links(filename2contents, only_for=[filename])
    
    with timeit('make_page()'):
        contents = filename2contents[filename]
        html = make_page(contents, head0, main_toc)
    
    if mathjax: 
        if preamble is not None:
            with timeit('add_mathjax_preamble()'):
                add_mathjax_preamble(html, preamble)
                
        with timeit('add_mathjax_call'):
            add_mathjax_call(html)
    
    if disqus:
        with timeit('disqus'):
            append_disqus(filename, html)

    with timeit('update_refs_'):
        update_refs_(filename, html, id2filename)

    with timeit('serialize'):
        result = str(html)
    
    with timeit('writing'): 
        fn = os.path.join(directory, filename)
        write_data_to_file(result, fn)
    
    with timeit('extracting assets'):
        extract_assets_from_file(fn, fn, assets_dir)


class Split(QuickApp):
    """ Splits the manual into files """

    def define_options(self, params):
        params.add_string('filename', help="""Input filename""")
        params.add_string('output_dir', help='Output directory')
        params.add_flag('disqus')
        params.add_flag('mathjax')
        params.add_string('preamble', default=None)
        params.add_flag('faster_but_imprecise')
        
    def define_jobs_context(self, context):
        ifilename = self.options.filename
        output_dir = self.options.output_dir
        mathjax = self.options.mathjax
        preamble = self.options.preamble
        disqus = self.options.disqus
        logger.setLevel(logging.DEBUG)
        
        soup = read_html_doc_from_file(ifilename)
        body = soup.html.body
        filename2contents = split_in_files(body)
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except:
                pass
        
        assets_dir = os.path.join(output_dir, 'assets')
        
        id2filename = get_id2filename(filename2contents)
        linkbase = 'link.html' # do not change (it's used by http://purl.org/dth)
        linkbasejs = 'link.js'
        lb = create_link_base(id2filename)
        write_data_to_file(str(lb), os.path.join(output_dir, linkbase))
        
        linkjs = create_link_base_js(id2filename)
        write_data_to_file(str(linkjs), os.path.join(output_dir, linkbasejs))
        
        if preamble:
            preamble = open(preamble).read()
            
        ids_to_use = []
        for k in list(id2filename):
            if not 'autoid' in k:
                ids_to_use.append(k)
        ids_to_use = sorted(ids_to_use)
        
        pointed_to =[]
        for k in ids_to_use:
            f = id2filename[k]
            if not f in pointed_to:
                pointed_to.append(f)
                
        data = ",".join(pointed_to)
        links_hash = get_md5(data)[:8]
        if self.options.faster_but_imprecise:
            links_hash = "nohash"

#         logger.debug('hash data: %r' % data)
#         logger.debug('hash value: %r' % links_hash)
        
        
        if True:
            context.comp(remove_spurious, output_dir, list(filename2contents))
        
        for filename, contents in filename2contents.items():
            contents_hash = get_md5(str(contents) + str(preamble))[:8]
            # logger.info('Set up %r' % filename)
            job_id = '%s-%s-%s' % (filename, links_hash, contents_hash)
            context.comp(split_file, ifilename, output_dir, filename, mathjax=mathjax, preamble=preamble,
                         disqus=disqus, id2filename=id2filename, assets_dir=assets_dir,
                         job_id=job_id)

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
                id_ = e.attrs['id'].replace(':section','')
                from mcdp_docs.composing.cli import remove_prefix

                if not 'autoid' in id_:
                    id_ = remove_prefix(id_)
                    url = 'http://purl.org/dt/master/' + id_
                    OTHER = '<p>Maybe try this link to find the version on master (no guarantees): <a href="%s">%s</a></p>' % (url,url)
                    OTHER += '\n<p>If that does not work, the section was renamed.</p>'
                else:
                    OTHER = ''     
            else:
                OTHER = ''
                
            data = spurious.replace('OTHER', OTHER)
#             print data
            write_data_to_file(data, fn)
            
spurious = """
<html>
<head><title>Spurious file</title></head>
<body> <!-- SPURIOUS -->

<h2>Spurious file</h2>
<p>This file is a spurious remain from earlier compilation.</p>

<p>If you are reached this file, it means that somebody is not using PURLs 
to link to parts of the duckiebook.</p>

OTHER

</body>
</html>
"""


