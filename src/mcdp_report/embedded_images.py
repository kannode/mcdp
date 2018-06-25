# -*- coding: utf-8 -*-
import base64
import cStringIO
import mimetypes
import os
import re

from PIL import Image
from bs4 import BeautifulSoup
from bs4.element import Tag
from contracts import contract
from contracts.utils import check_isinstance, raise_wrapped
from mcdp import logger
from mcdp_docs.location import HTMLIDLocation
from mcdp_docs.manual_constants import MCDPManualConstants
from mcdp_report.pdf_conversion import ConversionError
from mcdp_utils_misc import get_md5, write_data_to_file, get_mcdp_tmp_dir, make_sure_dir_exists
from mcdp_utils_xml import add_style

from .pdf_conversion import png_from_pdf


#### One direction
def data_encoded_for_src(data, ext):
    """ data =
        ext = png, jpg, ...

        returns "data: ... " sttring
    """
    from mcdp_web.images.images import get_mime_for_format  # XXX:  move

    encoded = base64.b64encode(data)
    mime = get_mime_for_format(ext)
    link = 'data:%s;base64,%s' % (mime, encoded)
    return link


#### Other direction (note mime, not ext)


@contract(returns='tuple(str,str)')
def get_mime_data_from_base64_string(data_ref):
    """ data_ref: data:<mime>;base64,

        Returns mime, data.
    """
    assert data_ref.startswith('data:')
    first, second = data_ref.split(';')
    mime = first[len('data:'):]
    assert second.startswith('base64,')
    data = second[len('base64,'):]
    # print('link %r' % data_ref[:100])
    # print('decoding %r' % data[:100])
    decoded = base64.b64decode(data)
    return mime, decoded


def extract_assets(html, basedir):
    """
        Extracts all embedded assets in A links
        encoded using data: and save them to file.

        These are all links of the type:

            <a href="data:****"/>

            <a href="data:****" download='filename'/>
    """
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    soup = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    for tag in soup.select('a[href]'):
        href = tag['href']
        if href.startswith('data:'):
            _mime, data = get_mime_data_from_base64_string(href)
            if tag.has_attr('download'):
                basename = tag['download']
            else:
                logger.warn('cannot find attr "download" in tag')
                # print tag
                continue
            print('extracting asset %s' % basename)
            filename = os.path.join(basedir, basename)
            write_data_to_file(data, filename)


def extract_img_to_file(soup, savefile):
    """
        Extracts all images data specified inline and saves them
        to a file.

        These are all links of the type:

            <img src="data:image/XXX:base64...."
            <image xlink:href="data: image">

        The function

            savefile: name, data -> use_this_src

        Saves a file called "name.ong" with the data "data"
        in the same directory as where the soup will be.

    """
    # first do this, otherwise we cannot embed the stuff

    # extract_svg_to_file(soup, savefile)
    # two problems:
    #   1) svg from Mathjax refers to other svg fragments
    #   2) we can extract our rendered svg fine, however, we cannot set
    #      the width reliably (we cannot override with max-width)

    n = 0
    n += extract_img_to_file_(soup, savefile, tagname="img", attrname="src")
    n += extract_img_to_file_(soup, savefile, tagname="image", attrname="xlink:href")
    return n


def extract_svg_to_file(soup, savefile):
    n = 0
    tot = 0
    for i, svg in enumerate(list(soup.select('svg'))):
        tot += 1
        if not svg.attrs.get('class', ''):
            # only do the ones we rendered #XXX
            continue

        #        <svg focusable="false" height="2.176ex" role="img" style="vertical-align: -0.505ex;" viewbox="0
        svg['xmlns'] = "http://www.w3.org/2000/svg"
        svg['version'] = "1.1"
        prefix = """<?xml version="1.0"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n"""
        img = Tag(name='img')
        if 'width' in svg.attrs:
            add_style(img, width=svg['width'] + 'pt', height=svg['height'] + 'pt')
            svg.attrs.pop('width')
            svg.attrs.pop('height')

        data = prefix + str(svg)
        md5 = get_md5(data)

        basename = 'svg-%03d-%s' % (i, md5)
        propose = basename + '.svg'
        url = savefile(propose, data)

        #         for k, v in svg.attrs.items():
        #             img[k] = v
        img['class'] = svg.attrs.get('class', '')

        if 'id' in svg:
            img['id'] = svg['id']
        img['src'] = url
        svg.replace_with(img)

    logger.debug('extract_svg_to_file: extracted %d/%d images from SVG tags.'
                 % (n, tot))


def extract_img_to_file_(soup, savefile, tagname, attrname):
    n = 0
    tot = 0
    for tag in soup.select(tagname):
        tot += 1
        if not attrname in tag.attrs:
            msg = 'No attr %r found for tag %s' % (attrname, tag)
            logger.warning(msg)
            continue
        src = tag.attrs[attrname]

        if not src.startswith('data:'):
            continue

        mime, data = get_mime_data_from_base64_string(src)

        # now we should make up the data
        if tag.has_attr('id'):
            basename = tag['id']
        else:
            md5 = get_md5(data)
            basename = 'data-from-%s-%s' % (tagname, md5)

        # Guess extension
        ext = get_ext_for_mime(mime)
        filename = basename + '.' + ext
        # src = "%s" % filename
        # ask what we should be using
        # print('saving file %s with %d data' % (filename, len(data)))
        use_src = savefile(filename, data)
        check_isinstance(use_src, str)
        tag[attrname] = use_src
        n += 1
    if False:
        logger.debug(('extract_img_to_file: extracted %d/%d images from %r tags, '
                      ' attribute %r.') % (n, tot, tagname, attrname))
    return n


def get_ext_for_mime(mime):
    """ Returns the extension (without the dot) """
    if False:
        if mime == 'image/jpg':
            logger.debug('warning: the correct mime is image/jpeg not "jpg".')

    known = {
        'image/svg+xml': 'svg',
        'image/jpeg': 'jpg',
        'image/jpg': 'jpg',
        'text/plain': 'txt',
        'image/png': 'png',
        'application/pdf': 'pdf',
    }
    if mime in known:
        return known[mime]

    suffix = mimetypes.guess_extension(mime)
    if not suffix:
        raise Exception('Cannot guess extension for MIME %r.' % mime)
    # comes with leading dot
    assert suffix.startswith('.')
    ext = suffix[1:]

    # fix some problems
    if ext == 'svgz':
        ext = 'svg'

    return ext







def embed_img_data(soup, resolve, raise_on_error,
                   res, location,
                   embed=True):
    """
        resolve: ref -> str  or None --- how to get the data

        if embed = True, embeds the data. Expects resolve to return the data.
        if embed = False, just resolves the links. Expects resolve to return the path.
    """


    img_extensions = MCDPManualConstants.embed_img_data_extensions

    def accept_href(tag0, href0):
        if href0.startswith('data:'):
            return False

        if href0.startswith('http'):
            msg = 'I will not embed remote files, such as\n   %s' % href0
            res.note_warning(msg, HTMLIDLocation.for_element(tag0, location))
            return False

        return True


#<link rel="icon" href="https://www2.duckietown.org/wp-content/uploads/2018/05/cropped-duckie2-192x192.png" sizes="192x192" />
    for tag in soup.select('link[rel=icon]'):
        print tag
        href = tag.attrs['href']
        if not accept_href(tag, href):
            continue

        sub_img_url(tag, 'href', resolve, img_extensions, raise_on_error, res, location, embed)

    for tag in soup.select('img[src]'):
        href = tag['src']

        if not accept_href(tag, href):
            continue

        sub_img_url(tag, 'src', resolve, img_extensions, raise_on_error, res, location, embed)


def sub_img_url(tag, ATT, resolve, img_extensions, raise_on_error, res, location, embed):
    href = tag[ATT]

    for ext in img_extensions:

        if not href.endswith('.' + ext):
            continue

        data = resolve(href)

        if data is None:
            msg = 'embed_img_data: Could not find file:\n     %s' % href

            if raise_on_error:
                raise Exception(msg)  # XXX
            else:
                res.note_error(msg, HTMLIDLocation.for_element(tag, location))
                continue
        file_data = data['data']
        realpath = data['realpath']

        check_isinstance(data, dict)

        if embed:
            tag[ATT] = data_encoded_for_src(file_data, ext)
        else:
            if not os.path.exists(realpath):
                msg = 'Expecting a path from %r, but does not exist %s' % (href, realpath)
                raise Exception(msg)  # XXX

            max_width = MCDPManualConstants.max_width_for_image
            try:
                tag[ATT] = get_link_to_image_file(realpath, max_width)
            except IOError as e:
                msg = 'Could not resize %s:' % realpath
                msg += '\n\n ' + str(e)
                res.note_error(msg, locations=HTMLIDLocation.for_element(tag, location))

        break

import tempfile
import errno

def is_writable(path):
    try:
        testfile = tempfile.TemporaryFile(dir = path)
        testfile.close()
    except OSError as e:
        if e.errno == errno.EACCES:  # 13
            return False
        e.filename = path
        raise
    return True

def get_link_to_image_file(filename, max_width):
    dirname = os.path.dirname(filename)
    basename, ext = os.path.splitext(os.path.basename(filename).lower())

    if ext not in ['.jpg', '.jpeg']:
        return filename

    if is_writable(dirname):
        dest = os.path.join(dirname, basename+'-resized-%d' % max_width+'.jpg')
    else:
        b = basename + '-' + get_md5(filename)[:4] + '.jpg'
        dest = os.path.join(get_mcdp_tmp_dir(), 'images', b)

    if os.path.exists(dest):
        return dest

    with open(filename) as f:
        im = Image.open(f)
        # print filename, im.size

        if im.size[0] <= max_width:
            return filename

        height = int(im.size[1]*max_width/im.size[0])
        new_size = (max_width, height)
        msg = 'Resizing image %s from %s to %s' % (filename, im.size, new_size)
        logger.info(msg)
        # print('resizing to %s in %s' % (str(new_size), dest))
        if not os.path.exists(dest):
            make_sure_dir_exists(dest)
            resized = im.resize(new_size)
            resized.save(dest)
        return dest


def embed_svg_images(soup, extensions=('png', 'jpg')):
    """
        SVG produced by dot have tags of the type

            <image xlink:href="a.jpg">

        If it is one of the extensions, these will be embedded so that
        we have

            <image xlink:href="data:image/jpg;base64,AVFJIRJVIEJVEI..">

    """
    HREF = 'xlink:href'
    for tag in soup.select('image'):
        href = tag[HREF]
        for ext in extensions:
            assert not '.' in ext
            if href.endswith('.' + ext):
                with open(href) as ff:
                    data = ff.read()
                tag[HREF] = data_encoded_for_src(data, ext)


def embed_pdf_images(soup, resolve, density, raise_on_error, res, location):
    """
        Converts PDFs to PNGs and embeds them
        resolve: filename --> string
    """
    for tag in soup.select('img'):
        if tag.has_attr('src') and tag['src'].lower().endswith('pdf'):
            embed_pdf_image(tag, resolve, density, raise_on_error, res=res, location=location)


def embed_pdf_image(tag, resolve, density, raise_on_error, res, location):
    assert tag.name == 'img'
    assert tag.has_attr('src')
    # print('!!embedding %s' % str(tag))
    # raise Exception(str(tag))
    # load pdf data
    src = tag['src']
    if src.startswith('http'):
        msg = 'I will not embed remote files, such as %s: ' % src
        logger.warning(msg)

    found = resolve(src)
    if found is None:
        msg = 'Could not find PDF file %r.' % src
        if raise_on_error:
            raise Exception(msg)  # xxx
        else:
            # note_error2(tag, 'Resource error', msg, ['missing-image'])
            res.note_error(msg, HTMLIDLocation.for_element(tag, location))
            return

    data_pdf = found['data']
    _realpath = found['realpath']
    # convert PDF to PNG
    # density = pixels per inch
    try:
        data_png = png_from_pdf(data_pdf, density=density)
    except ConversionError as e:
        msg = 'I was not able to convert the PDF "%s" to PNG.' % tag['src']
        if raise_on_error:
            raise_wrapped(ConversionError, e, msg, compact=True)
        else:
            # note_error2(tag, 'Conversion error', msg, [])
            res.note_error(msg, HTMLIDLocation.for_element(tag, location))
        return

    # get PNG image size in pixels
    width_px, height_px = get_pixel_width_height_of_png(data_png)
    # compute what was the original width of PDF in points

    width_in = width_px / float(density)
    height_in = height_px / float(density)

    latex_options = tag.get('latex-options', '')
    props = parse_includegraphics_option_string(latex_options)

    if 'height' in props:
        msg = ('Cannot deal with "height" yet: latex_options = %s' % latex_options)
        res.note_warning(msg, HTMLIDLocation.for_element(tag, location))

    if 'scale' in props:
        scale = float(props['scale'])
        use_width_in = width_in * scale
        use_height_in = height_in * scale
    elif 'width' in props:
        try:
            use_width_in = get_length_in_inches(props['width'])
        except ValueError as e:
            logger.error('Cannot interpret %s: %s' % (latex_options, e))
            use_width_in = 5.0
        ratio = height_in / width_in
        use_height_in = use_width_in * ratio
    else:
        use_width_in = width_in
        use_height_in = height_in

    # Add it before so that we can override
    add_style(tag, after=False, width='%sin' % use_width_in, height='%sin' % use_height_in)
    tag['size_in_pixels'] = '%s, %s' % (width_px, height_px)
    # encode
    tag['src'] = data_encoded_for_src(data_png, 'png')


def get_pixel_width_height_of_png(data_png):
    from PIL import Image
    im = Image.open(cStringIO.StringIO(data_png))  # @UndefinedVariable
    width_px, height_px = im.size  # (wid
    return width_px, height_px


def parse_includegraphics_option_string(latex_options):
    """ Parses a list of the type "a=b,c=d,h,f=2" in a dict
        Entries like "h" get assigned = True.
    """
    props = {}
    for assignment in re.split(',', latex_options):
        tokens = list(re.split('=', assignment))
        if len(tokens) == 2:
            props[tokens[0]] = tokens[1]
        elif len(tokens) == 1:
            props[tokens[0]] = True
        else:
            raise ValueError((latex_options, tokens))
    return props


def get_length_in_inches(s):
    """ "1cm" = 0.393 """
    #     s = s.replace('\\columnwidth', '8.')
    inpoints = {'cm': 0.393, 'in': 1.0,
                '\\textwidth': 6.0}
    for unit, ininches in inpoints.items():
        if unit in s:
            digits = s[:s.index(unit)]
            num = float(digits)
            res = num * ininches
            print ('%r = %s inches (digits: %s)' % (s, res, digits))
            return res
    msg = 'Cannot interpreted length %r.' % s
    raise ValueError(msg)
