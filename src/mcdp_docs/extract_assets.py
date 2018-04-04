import os
import shutil

from bs4.element import Tag

from compmake.utils.filesystem_utils import make_sure_dir_exists
from mcdp_cli.utils_mkdir import mkdirs_thread_safe
from mcdp_report.embedded_images import extract_img_to_file
from mcdp_utils_misc import write_data_to_file
from mcdp_utils_misc.string_utils import get_md5
from mcdp_utils_xml import read_html_doc_from_file, write_html_doc_to_file
from mcdp_utils_xml.project_text import gettext
from quickapp import QuickAppBase

from .logs import logger


class ExtractAssets(QuickAppBase):
    """
        Extracts the image assets from HTML and creates external files.

        Usage:

            %prog  --input input.html --output out.html

        It puts the assets in the directory

            out.html.assets

    """

    def define_program_options(self, params):
        params.add_string('input', help="""Input HTML file""")
        params.add_string('output', help="""Output HTML file""")
        params.add_string('assets', help="""Where to put the assets""",
                          default=None)

    def go(self):
        fi = self.options.input
        fo = self.options.output
        if self.options.assets is None:
            assets_dir = fo + '.assets'
        else:
            assets_dir = self.options.assets

        extract_assets_from_file(fi, fo, assets_dir)


extract_assets_main = ExtractAssets.get_sys_main()


def extract_assets_from_file(fi, fo, assets_dir):
#     logger.info('Extracting assets ___')
#     logger.info('Input: %s' % fi)
#     logger.info('Output: %s' % fo)
#     logger.info('Using assets dir: %s' % assets_dir)

    make_sure_dir_exists(fo)
    if not os.path.exists(assets_dir):
        mkdirs_thread_safe(assets_dir)

    soup = read_html_doc_from_file(fi)
    s0 = os.path.getsize(fi)

    def savefile(filename_hint, data):
        """ must return the url (might be equal to filename) """
        where = os.path.join(assets_dir, filename_hint)
        write_data_to_file(data, where, quiet=True)
        relative = os.path.relpath(where, os.path.dirname(fo))
        return relative

    extract_img_to_file(soup, savefile)

    save_images_locally(soup, fo, assets_dir)
    save_css(soup, fo, assets_dir)
    write_html_doc_to_file(soup, fo, quiet=True)

    if False:
        s1 = os.path.getsize(fo)
        inmb = lambda x: '%.1f MB' % (x / (1024.0 * 1024))
        msg = 'File size: %s -> %s' % (inmb(s0), inmb(s1))
        logger.info(msg)


def save_css(soup, fo, assets_dir):
    for style in soup.select('head style'):
        data = style.text.encode(errors='ignore')
        md5 = get_md5(data)
        basename = 'style-%s.css' % (md5)
        dest_abs = os.path.join(assets_dir, basename)
        dest_rel = os.path.relpath(dest_abs, os.path.dirname(fo))
        if not os.path.exists(dest_abs):
            with open(dest_abs, 'w') as f:
                f.write(data)

        link = Tag(name='link')
        link.attrs['rel'] = 'stylesheet'
        link.attrs['type'] = 'text/css'
        link.attrs['href'] = dest_rel

        style.replace_with(link)
#        print link


def save_images_locally(soup, fo, assets_dir):
    for tag in soup.select('img[src]'):
        src = tag.attrs['src']
        # check if not relative path
        if src.startswith('/') or src.startswith('..'):

            if not os.path.exists(src):
                msg = 'Could not find resource %s' % src
                logger.error(msg)
                continue

            with open(src) as f:
                data = f.read()
                md5 = get_md5(data)

            _, ext = os.path.splitext(src)
            basename = 'data-from-img-%s%s' % (md5, ext)
            dest_abs = os.path.join(assets_dir, basename)
            dest_rel = os.path.relpath(dest_abs, os.path.dirname(fo))

            if not os.path.exists(dest_abs):
                shutil.copy(src, dest_abs)
#            print('new link: %s' % dest_rel)
#            print('new res: %s' % dest_abs)
            tag.attrs['src'] = dest_rel


if __name__ == '__main__':
    extract_assets_main()
