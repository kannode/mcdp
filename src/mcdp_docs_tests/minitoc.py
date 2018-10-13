# # -*- coding: utf-8 -*-
# from __future__ import print_function
#
# from compmake.utils.filesystem_utils import make_sure_dir_exists
# from comptests.registrar import run_module_tests, comptest
# from contracts.utils import indent
# from mcdp_docs.location import LocationUnknown
# from mcdp_docs.manual_join_imp import manual_join, split_in_files, DocToJoin
# from mcdp_docs.pipeline import render_complete
# from mcdp_docs.toc_number import number_styles, render_number
# from mcdp_docs.tocs import generate_toc, InvalidHeaders, fix_ids_and_add_missing
# from mcdp_library.library import MCDPLibrary
# from mcdp_tests import logger
# from mcdp_utils_misc import AugmentedResult
# from mcdp_utils_xml import bs
#
#
# @comptest
# def test_toc():
#     s = """
# <html>
# <head></head>
# <body>
# <h1 id='one'>One</h1>
#
# <p>a</p>
#
# <minitoc/>
#
# <h2 id='two'>Two</h2>
#
# <p>a</p>
#
# <h3 id='three'>Three</h3>
#
# <h2 id='four'>Four</h2>
#
# <p>a</p>
# </body>
# </html>
#     """
#     soup = bs(s)
#     #     print(soup)
#     #     body = soup.find('body')
#
#     # first time it should fail
#     try:
#         _toc = generate_toc(soup)
#     except InvalidHeaders as e:
#         #         > InvalidHeaders: I expected that this header would start with either part:,app:,sec:.
#         #         > <h1 id="one">One</h1>
#         pass
#     else:
#         raise Exception()
#
#     soup = bs(s)
#     fix_ids_and_add_missing(soup, 'prefix-', AugmentedResult(), LocationUnknown())
#     generate_toc(soup)
#
#
#
#     s = str(soup)
#     expected = ['sec:one', 'sub:two']
#     #     print(indent(s, 'transformed > '))
#     for e in expected:
#         assert e in s
#
