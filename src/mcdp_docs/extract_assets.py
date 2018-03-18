from compmake.utils.filesystem_utils import make_sure_dir_exists
from mcdp_report.embedded_images import extract_img_to_file
from mcdp_utils_misc import write_data_to_file
from mcdp_utils_xml import read_html_doc_from_file, write_html_doc_to_file
import os

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
        os.makedirs(assets_dir)

    soup = read_html_doc_from_file(fi)
    s0 = os.path.getsize(fi)
    
    def savefile(filename_hint, data):
        """ must return the url (might be equal to filename) """
        where = os.path.join(assets_dir, filename_hint)
        write_data_to_file(data, where)
        relative = os.path.relpath(where, os.path.dirname(fo))
        return relative
    
    extract_img_to_file(soup, savefile)

    write_html_doc_to_file(soup, fo)
    if False:
        s1 = os.path.getsize(fo)
        inmb = lambda x: '%.1f MB' % (x / (1024.0*1024)) 
        msg = 'File size: %s -> %s' % (inmb(s0), inmb(s1))
        logger.info(msg)

    
if __name__ == '__main__':
    extract_assets_main()
    