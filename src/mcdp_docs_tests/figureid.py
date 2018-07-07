from __future__ import print_function
from comptests.registrar import comptest, run_module_tests
from mcdp_docs import render_complete

from mcdp_library import MCDPLibrary

s = """

<figure id="myID">
  inside 1
</figure>

<div figure-id="fig:DUE">
  inside 2
</div>
 
"""

@comptest
def figureid1():

    library = MCDPLibrary()
    raise_errors = True
    realpath = 'transformations.py'
    s2 = render_complete(library, s, raise_errors, realpath, generate_pdf=False)
    print(s2)

    assert  'id="myID"' not in s2
    assert 'id="fig:myID"'  in s2

    assert 'id="fig:DUE"'  in s2


if __name__ == '__main__':
    run_module_tests()
