from comptests.registrar import comptest, run_module_tests


@comptest
def task_markers_test1():
    pass
    # s = "<p>We should do this (TODO)</p>"
    # e = """<p class="status-todo">We should do this (TODO)</p>"""
    # soup = bs(s.strip())
    #
    # res = AugmentedResult()
    # location = LocationUnknown()
    # substitute_task_markers(soup, res, location)
    #
    # o = to_html_stripping_fragment(soup)
    # #print o
    # assert_equal(o, e)
    #


if __name__ == '__main__':
    run_module_tests()
