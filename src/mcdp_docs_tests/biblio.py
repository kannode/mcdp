from mcdp_docs.read_bibtex import run_bibtex2html
from comptests.registrar import comptest, run_module_tests

@comptest
def test_bibliography1():
    contents = """
@book{siciliano07handbook,
 author = {Siciliano, Bruno and Khatib, Oussama},
 title = {Springer Handbook of Robotics},
 year = {2007},
 isbn = {354023957X},
 publisher = {Springer-Verlag New York, Inc.},
 address = {Secaucus, NJ, USA},
}
    """
    result_aug = run_bibtex2html(contents)
    result = result_aug.get_result()
    print(result)
    assert '<cite id="bib:siciliano07handbook">' in result
    # We should have removed the link
    assert not 'bib</a>' in result
    assert not '[' in result

if __name__ == '__main__':
    run_module_tests()
