from collections import OrderedDict
import os

from compmake.structures import Promise
from compmake.utils.friendly_path_imp import friendly_path
from contracts import contract
from contracts.utils import check_isinstance
from mcdp_docs.logs import logger
from mcdp_docs.manual_join_imp import DocToJoin
from mcdp_docs.mcdp_render_manual import render_book
from mcdp_docs.source_info_imp import get_source_info
from mcdp_docs.vols.recipe import RecipeCommandDynamic
from mcdp_utils_misc.augmented_result import AugmentedResult
from mcdp_utils_misc.string_utils import get_md5


class RenderCommand(RecipeCommandDynamic):

    def __init__(self):
        pass

    @contract(bs_aug=AugmentedResult, returns=Promise)
    def go_dynamic(self, context, bs_aug):
        bs = bs_aug.get_result()
        filenames = bs.files
        src_dirs = bs.resources_dirs
        render_jobs_result = render_jobs(context, filenames, src_dirs)
        return context.comp(merge_jobs, bs_aug, render_jobs_result)

    def __str__(self):
        return 'Render'


@contract(bs_aug=AugmentedResult, render_jobs_result_aug=AugmentedResult)
def merge_jobs(bs_aug, render_jobs_result_aug):
    bs_aug.merge(render_jobs_result_aug)

    bs = bs_aug.get_result()

    bs.variables['rendered'] = render_jobs_result_aug.get_result()

    return bs_aug


def render_jobs(context, filenames, src_dirs):
    docname2aug = OrderedDict()
    for i, filename in enumerate(filenames):
        check_isinstance(filename, str)
        logger.info('adding document %s ' % friendly_path(filename))

        docname, _ = os.path.splitext(os.path.basename(filename))

        contents = open(filename).read()
        contents_hash = get_md5(contents)[:8]
        # because of hash job will be automatically erased if the source changes
        out_part_basename = '%03d-%s-%s' % (i, docname, contents_hash)
        job_id = '%s-%s-%s' % (docname, get_md5(filename)[:8], contents_hash)

        source_info = get_source_info(filename)

        generate_pdf = False
        use_mathjax = False
        symbols = None
        raise_errors = False
        filter_soup = None
        extra_css = None

        html_contents_aug = context.comp(render_book_aug,
                                         generate_pdf=generate_pdf,
                                         src_dirs=src_dirs,
                                           data=contents, realpath=filename,
                                           use_mathjax=use_mathjax,
                                           symbols=symbols,
                                            raise_errors=raise_errors,
                                           main_file=None,
                                           out_part_basename=out_part_basename,
                                           filter_soup=filter_soup,
                                           extra_css=extra_css,
                                           job_id=job_id)

        doc = DocToJoin(docname=out_part_basename, contents=html_contents_aug,
                        source_info=source_info)
        docname2aug[out_part_basename] = tuple(doc)
    return context.comp(render_jobs_join, docname2aug)


def render_jobs_join(docname2aug):
    aug = AugmentedResult()
    res = []
    for docname, doc_ in docname2aug.items():
        doc = DocToJoin(*doc_)
        aug.merge(doc.contents, docname)

        contents = doc.contents.get_result()
        doc = doc._replace(contents=contents)
        res.append(tuple(doc))
    aug.set_result(res)
    return aug


def render_book_aug(*args, **kwargs):
    aug = AugmentedResult()
    html = render_book(*args, **kwargs)
    aug.set_result(html)
    return aug

