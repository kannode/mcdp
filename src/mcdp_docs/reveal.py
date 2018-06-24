# -*- coding: utf-8 -*-
import shutil

import requests
from bs4 import Tag, NavigableString

from mcdp_docs import logger
from mcdp_docs.embed_css import embed_css_files
from mcdp_report.html import get_css_filename
from mcdp_utils_misc import write_data_to_file, AugmentedResult
from mcdp_utils_xml import bs, copy_contents_into, copy_contents_into_beginning, add_class, get_parents_names


def create_slides(soup):
    res = AugmentedResult()

    header = soup.find('h1', attrs=dict(type='slides'))

    if header is None:
        # logger.debug('No slides here')
        return

    _id = header.attrs['id'].replace('sec:', '')
    _id_section = (_id + ':section')
    section = soup.find(id=_id_section)
    if section is None:
        msg = 'Could not find section by ID %r' % _id_section
        logger.error(msg)
        return

    section.extract()

    body = soup.find('body')
    body.attrs['type'] = 'slides'
    body = soup.find('div', attrs={'class': 'super'})

    div = Tag(name='div')
    div.attrs['class'] = 'reveal'
    body.append(div)

    div_slides = Tag(name='div')
    div_slides.attrs['class'] = 'slides'

    div.append(div_slides)

    for subsection in section.select('section[level=sub]'):
        if 'without-header-inside' in subsection.attrs['class']:
            continue

        # print 'extracting', subsection.attrs
        subsection.extract()
        div_slides.append(subsection)

    div_slides.insert(0, section)

    sub_notes(div_slides)
    sub_markers(div_slides)

    stylesheet = "v_manual_reveal"
    add_stylesheet(soup, stylesheet)
    embed_css_files(soup)
    create_reveal(soup, res)


def download_reveal(output_dir):
    res = AugmentedResult()
    url = "https://github.com/hakimel/reveal.js/archive/3.6.0.zip"
    target = os.path.join(output_dir, 'revealjs')
    dest = os.path.join(output_dir, 'reveal-3.6.0.zip')

    if os.path.exists(target):
        logger.debug('skipping downloading because target exists: %s' % target)

    else:

        caches = ['/project/reveal-3.6.0.zip']

        for c in caches:
            if os.path.exists(c):
                shutil.copy(c, dest)
                break

        else:

            if True or not os.path.exists(dest):
                logger.info('Downloading %s' % url)

                response = requests.get(url, stream=True)

                with open(dest, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)

                # logger.info('downloaded %1.fMB' % (len(data) / (1000.0 * 1000)))
                # write_data_to_file(data, dest)
            logger.info(dest)

        target_tmp = target + '.tmp'
        import zipfile
        zip_ref = zipfile.ZipFile(dest, 'r')
        zip_ref.extractall(target_tmp)
        zip_ref.close()

        actual = os.path.join(target_tmp, 'reveal.js-3.6.0')
        os.rename(actual, target)
        logger.debug('extracted to %r' % target)

    check = [
        "plugin/notes/notes.js",
        "plugin/math/math.js",
        "lib/js/head.min.js",
        "js/reveal.js",
    ]
    for c in check:
        fn = os.path.join(target, c)
        if not os.path.exists(fn):
            msg = 'Incomplete reveal download, not found: %s' % fn
            res.note_error(msg)
    return res


def add_stylesheet(html, stylesheet):
    head = html.find('head')
    link = Tag(name='link')
    link['rel'] = 'stylesheet'
    link['type'] = 'text/css'
    link['href'] = get_css_filename('compiled/%s' % stylesheet)
    head.append('\n')
    head.append(link)
    head.append('\n')


import os


def write_slides(res, outdir):
    slides = res.get_result()

    for id_slides, html in slides.items():
        filename = os.path.join(outdir, id_slides + '.html')
        data = str(html)
        write_data_to_file(data, filename)


def sub_notes(soup):
    for e in soup.select('blockquote'):
        e.name = 'aside'
        add_class(e, 'notes')


def sub_markers(soup):
    for ns in list(soup.descendants):
        if isinstance(ns, NavigableString):
            # print('considering "%s"' % ns)
            marker = u'▶'
            if 'code' in get_parents_names(ns):
                # consider the char `▶`
                continue

            if marker in ns:
                ns2 = ns.replace(marker, '')
                parent = ns.parent

                if parent.parent and parent.parent.name == 'li':
                    parent = parent.parent
                else:
                    if 'figure-conv-to-div' in parent.attrs.get('class', ''):
                        parent = parent.parent.parent

                add_class(parent, 'fragment')

                ns.replace_with(ns2)


def create_reveal(soup, res):
    assert isinstance(soup, Tag)

    body = soup.find('body')

    head = soup.find('head')
    if head is None:
        msg = 'Could not find <head>'
        raise Exception(msg)
    if body is None:
        msg = 'Could not find <body>'
        raise Exception(msg)

    # base = 'https://cdnjs.cloudflare.com/ajax/libs/reveal.js/3.6.0'
    # base = "http://cdn.rawgit.com/hakimel/reveal.js/3.5.0"
    base = 'revealjs'

    # Remove this:
    # <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.0/MathJax.js?config=TeX-MML-AM_CHTML"></script>
    for script in list(soup.select('script[src]')):
        if 'MathJax.js' in script.attrs['src']:
            script.extract()

    header = """
        <link rel="stylesheet" href="BASE/css/reveal.css">
    	
    """
    header = header.replace('BASE', base)

    copy_contents_into_beginning(bs(header), head)

    # language=html
    footer = """
        <script src="BASE/lib/js/head.min.js"></script>
        <script src="BASE/js/reveal.js"></script>
		<script>
        options = {
            transition: 'none',
            center: false,
        	dependencies: [
        		{ src: 'BASE/plugin/notes/notes.js', async: true },
                        
                        
                // MathJax
                { src: 'BASE/plugin/math/math.js', async: true }
        	],
        	// The "normal" size of the presentation, aspect ratio will be preserved
            // when the presentation is scaled to fit different resolutions. Can be
            // specified using percentage units.
            width: 960,
            height: 700,

            // Factor of the display size that should remain empty around the content
            margin: 0.1,
            slideNumber: true,
            history: true, // change the url fragment
        };
        Reveal.initialize(options);
		</script>
	"""
    footer = footer.replace('BASE', base)

    copy_contents_into(bs(footer), body)

    """
    <section class="without-header-inside" level="book">

    <section class="without-header-inside" level="part">

    """

    s1 = body.find('section', attrs=dict(level="book"))
    if s1:
        s1.name = 'div'
        s1.attrs['class'] = 'reveal'

    s2 = body.find('section', attrs=dict(level="part"))
    if s2:
        s2.name = 'div'
        s2.attrs['class'] = 'slides'
