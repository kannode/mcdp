# -*- coding: utf-8 -*-
from __future__ import print_function

from compmake.utils.filesystem_utils import make_sure_dir_exists
from comptests.registrar import run_module_tests, comptest
from contracts.utils import indent
from mcdp_docs.location import LocationUnknown
from mcdp_docs.manual_join_imp import manual_join, split_in_files, DocToJoin
from mcdp_docs.pipeline import render_complete
from mcdp_docs.toc_number import number_styles, render_number
from mcdp_docs.tocs import generate_toc, InvalidHeaders, fix_ids_and_add_missing
from mcdp_library.library import MCDPLibrary
from mcdp_tests import logger
from mcdp_utils_misc import AugmentedResult
from mcdp_utils_xml import bs


@comptest
def test_toc():
    s = """
<html>
<head></head>
<body>
<h1 id='one'>One</h1>

<p>a</p>

<h2 id='two'>Two</h2>

<p>a</p>

<h3 id='three'>Three</h3>

<h2 id='four'>Four</h2>

<p>a</p>
</body>
</html>
    """
    soup = bs(s)
    #     print(soup)
    #     body = soup.find('body')

    # first time it should fail 
    try:
        _toc = generate_toc(soup)
    except InvalidHeaders as e:
        #         > InvalidHeaders: I expected that this header would start with either part:,app:,sec:.
        #         > <h1 id="one">One</h1>
        pass
    else:
        raise Exception()

    soup = bs(s)
    fix_ids_and_add_missing(soup, 'prefix-', AugmentedResult(), LocationUnknown())
    generate_toc(soup)

    s = str(soup)
    expected = ['sec:one', 'sub:two']
    #     print(indent(s, 'transformed > '))
    for e in expected:
        assert e in s


@comptest
def test_toc_first():
    s = """
<p>Before everything</p>
<h1 id='booktitle' nonumber="1" notoc="1">Booktitle</h1>

<p>A figure</p>

<h1 id='mtoc' nonumber="1" notoc="1">toc</h1>

<p> This is my toc </p>

 
<h1 id='part:part1'>Part1</h1>

<p>a</p>

<h1 id='sec:one'>One</h1>

<p>a</p>
 
    """
    files_contents = [DocToJoin(docname='a', contents=s, source_info=None)]

    stylesheet = 'v_manual_blurb_ready'
    res = manual_join(template=template, files_contents=files_contents,
                      stylesheet=stylesheet)

    soup = bs(res)

    #     print(indent(soup.prettify(), 't > '))
    #     body = soup.find('body')
    filename2contents = split_in_files(soup)
    print(list(filename2contents.keys()))
    index = filename2contents['index.html']

    print(indent(index, 'index > '))
    s = str(index)
    assert 'Before everything' in s


# XXX: erratic behavior
# @comptest
def test_toc2():
    s = """
<html>
<head></head>
<body>
<h1>One</h1>
<h1>Two</h1>
<h1>Three</h1>
<p></p>

<h2>A</h2>

<h2>B</h2>

<h2>C</h2>

<h3>a</h3>
<h3>b</h3>
<h3>c</h3>

</body>
</html>
    """
    soup = bs(s)
    #     print(soup)
    #     body = soup.find('body')
    fix_ids_and_add_missing(soup, 'prefix', AugmentedResult(), LocationUnknown())
    assert soup.find(id='sub:prefix-5') is not None
    #     <fragment>
    # <h1 id="sec:prefix--1">One</h1>
    # <h1 id="sec:prefix--2">Two</h1>
    # <h1 id="sec:prefix--3">Three</h1>
    # <p></p>
    # <h2 id="sub:prefix--4">A</h2>
    # <h2 id="sub:prefix--5">B</h2>
    # <h2 id="sub:prefix--6">C</h2>
    # <h3 id="subsub:prefix--7">a</h3>
    # <h3 id="subsub:prefix--8">b</h3>
    # <h3 id="subsub:prefix--9">c</h3>
    # </fragment>
    print(soup)

    _toc = generate_toc(soup)
    s = str(soup)


#     expected = ['sec:one', 'sub:two']
#     print(indent(s, 'transformed > '))
#     for e in expected:
#         assert e in s

@comptest
def test_render_number():
    styles = sorted(number_styles)
    numbers = range(0, 55)
    for s in styles:
        _r = [render_number(_, s) for _ in numbers]


#         print('%s: %s' % (s, r))

@comptest
def test_toc_numbers1():
    s = r"""
    
<div id='toc'></div>

# Part One {#part:one}

# Chapter One

## Sub One_point_One

Referring to [](#fig:One) and [](#fig:Two) and [](#tab:One).

Also referring only with numbers: 
<a href="#fig:One" class='only_number'></a>,
<a href="#fig:Two" class='only_number'></a>,
<a href="#tab:One" class='only_number'></a>.

<s figure-id="fig:One">Figure One</s>

### Sub sub One_point_One_point_One
#### Par a
#### Par b


## Sub One_point_Two

Referring to subfigures [](#subfig:child1) and [](#subfig:child2).
  
<div figure-id="fig:parent">
    <div figure-id="subfig:child1" figure-caption="child1">
    child1
    </div>
    <div figure-id="subfig:child2" figure-caption="child2">
    child2
    </div>
</div>


<div figure-id="code:code1">
    <pre><code>code1</code></pre>
</div>

## Sub with `code` in the <k>name</k>

# Chapter Two 

<s figure-id="fig:Two">Figure Two</s>

<s figure-id="tab:One">Table One</s>

## Sub Two_point_One

# Part Two {#part:two}

# Chapter Three

\begin{definition}[DefinitionA]\label{def:A}Definition A\end{definition}
\begin{defn}[DefinitionA2]\label{def:A2}Definition A2\end{defn}

\begin{proposition}[PropositionB]\label{prop:B}Proposition B\end{proposition}

\begin{problem}[ProblemC]\label{prob:C}Problem C\end{problem}

\begin{example}[exampleD]\label{exa:D}...\end{example}
\begin{remark}[remarkE]\label{rem:E}...\end{remark}
\begin{lemma}[lammaF]\label{lem:F}...\end{lemma}
\begin{theorem}[theoremG]\label{thm:G}...\end{theorem}
\begin{thm}[theoremG2]\label{thm:G2}...\end{thm}

Citing: 
[](#def:A),
[](#prop:B),
[](#prob:C),
[](#exa:D),
[](#rem:E),
[](#lem:F),
[](#thm:G).

Citing full name:
<a href="#def:A" class="number_name"></a>,
<a href="#prop:B" class="number_name"></a>,
<a href="#prob:C" class="number_name"></a>,
<a href="#exa:D" class="number_name"></a>,
<a href="#rem:E" class="number_name"></a>,
<a href="#lem:F" class="number_name"></a>,
<a href="#thm:G" class="number_name"></a>.

Citing only name:
<a href="#def:A" class="only_name"></a>,
<a href="#prop:B" class="only_name"></a>,
<a href="#prob:C" class="only_name"></a>,
<a href="#exa:D" class="only_name"></a>,
<a href="#rem:E" class="only_name"></a>,
<a href="#lem:F" class="only_name"></a>,
<a href="#thm:G" class="only_name"></a>.


Citing only number:
<a href="#def:A" class="only_number"></a>,
<a href="#prop:B" class="only_number"></a>,
<a href="#prob:C" class="only_number"></a>,
<a href="#exa:D" class="only_number"></a>,
<a href="#rem:E" class="only_number"></a>,
<a href="#lem:F" class="only_number"></a>,
<a href="#thm:G" class="only_number"></a>.


# Appendices {#part:appendices}

# Appendix A {#app:A}
# Appendix B {#app:B}
## App sub B_point_One 
### App subsub B_point_One_point_One

    """
    library = MCDPLibrary()
    raise_errors = True
    realpath = __name__
    s = render_complete(library, s, raise_errors, realpath)

    files_contents = [DocToJoin(docname='a', contents=s, source_info=None)]
    stylesheet = 'v_manual_blurb_ready'
    res_aug = manual_join(template=template, files_contents=files_contents, stylesheet=stylesheet)
    res = res_aug.get_result()
    fn = 'out/comptests/test_toc_numbers1.html'  # XXX: write on test folder
    make_sure_dir_exists(fn)
    logger.info('written on %s' % fn)
    with open(fn, 'w') as f:
        f.write(res)


template = """<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        </head><body></body></html>
        """

if __name__ == '__main__':
    run_module_tests()
