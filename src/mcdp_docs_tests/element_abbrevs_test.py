from mcdp_docs.location import LocationUnknown
from mcdp_utils_misc import AugmentedResult
from nose.tools import assert_equal

from comptests.registrar import comptest, run_module_tests
from mcdp_docs.elements_abbrevs import substitute_special_paragraphs
from mcdp_utils_xml import bs, to_html_stripping_fragment


@comptest
def elements_abbrevs_test1():
    s = "<p>TODO: paragraph</p>"
    e = """<div class="todo-wrap"><p class="todo">paragraph</p></div>"""
    soup = bs(s.strip())

    res = AugmentedResult()
    location = LocationUnknown()
    substitute_special_paragraphs(soup, res, location)
    
    o = to_html_stripping_fragment(soup)
    #print o
    assert_equal(o, e)
    

@comptest
def elements_abbrevs_test2():
    s = "<p>TODO: paragraph <strong>Strong</strong></p>"
    e = """<div class="todo-wrap"><p class="todo">paragraph <strong>Strong</strong></p></div>"""
    soup = bs(s.strip())

    res = AugmentedResult()
    location = LocationUnknown()
    substitute_special_paragraphs(soup, res, location)
    
    o = to_html_stripping_fragment(soup)
    #print o
    assert_equal(o, e)
    
    
if __name__ == '__main__':
    run_module_tests()
