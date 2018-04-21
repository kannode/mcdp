# -*- coding: utf-8 -*-
import datetime
from collections import namedtuple

import mcdp
from mcdp import MCDPConstants


class MCDPManualConstants(object):
    activate_tilde_as_nbsp = False

    pdf_metadata = 'pdf_metadata.txt'
    pdf_metadata_template = pdf_metadata + '.in'
    main_template = '00_main_template.html'

    macros = {}
    macros['PYMCDP_VERSION'] = mcdp.__version__
    # 'July 23, 2010'
    now = datetime.datetime.now()
    today = datetime.date.today()
    macros['PYMCDP_COMPILE_DATE'] = today.strftime("%B %d, %Y")
    macros['PYMCDP_COMPILE_TIME'] = now.strftime("%I:%M%p")
    macros['PYMCDP_COMPILE_DATE_SHORT'] = today.strftime('%Y-%m-%d')
    macros['AUTHOR'] = 'Andrea Censi'
    macros['TITLE'] = 'Formal tools for co-design'
    macros['TITLE_CAPS'] = 'Formal Tools for Co-Design'
    macros['SUBJECT'] = 'all about co-design'

    keywords = ['co-design', 'optimization', 'systems']
    macros['KEYWORDS_PDF'] = "; ".join(keywords)
    macros['KEYWORDS_HTML'] = ", ".join(keywords)
    macros['PRODUCER'] = 'PyMCDP %s + PrinceXML + pdftk' % mcdp.__version__
    macros['GENERATOR'] = macros['PRODUCER']
    macros['CREATOR'] = 'PyMCDP %s' % mcdp.__version__

    # D:19970915110347
    macros['CREATION_DATE_PDF'] = "D:" + now.strftime("%Y%m%d%H%M%S-05'00'")
    macros['MOD_DATE_PDF'] = macros['CREATION_DATE_PDF']

    macros['RENDER_PARAMS'] = str({
        'pdf_to_png_dpi': MCDPConstants.pdf_to_png_dpi,
    })

    macros['MCDPConstants'] = MCDPConstants.__dict__  # @UndefinedVariable

    CLASS_ONLY_NUMBER = 'only_number'
    CLASS_ONLY_NAME = 'only_name'
    CLASS_NUMBER_NAME = 'number_name'

    ID_PUT_BIB_HERE = 'put-bibliography-here'

    OTHER_THINGS_TO_INDEX = ['figure', 'div', 'cite']


    allowed_prefixes_h = {
        'h1': ['sec', 'app', 'part'],
        'h2': ['sub', 'appsub'],
        'h3': ['subsub', 'appsubsub'],
        'h4': ['par'],
        'h5': ['subpar'],
    }

    HEADERS_TO_FIX = HEADERS_TO_INDEX = list(allowed_prefixes_h)
    # HEADERS_TO_FIX = ['h1', 'h2', 'h3', 'h4', 'h5']
    # HEADERS_TO_INDEX = ['h1', 'h2', 'h3', 'h4', 'h5']
    all_possible_prefixes_that_can_be_implied = [
        'part', 'sec', 'sub', 'subsub', 'par', 'subpar', 'app', 'appsub', 'appsubsub',
        'fig', 'tab', 'code',
        'def', 'eq', 'rem', 'lem', 'prob', 'prop', 'exa', 'thm',
    ]
    
    ATTR_NOTOC = 'notoc'
    ATTR_NONUMBER = 'nonumber'
    exclude_from_toc = [
        'subsub', 'par', 'subpar', 'appsubsub',
        'fig', 'subfig',
        'code', 'tab',
        'def', 'eq', 'rem', 'lem', 'prob', 'prop', 'exa', 'thm']

    counters = [
        'part', 'app', 'sec', 'sub', 'subsub', 'appsub', 'appsubsub', 'par', 'subpar',
        'fig', 'tab', 'subfig', 'code',
        'exa', 'rem', 'lem', 'def', 'prop', 'prob', 'thm',
    ]

    # This is the TOC placeholder
    TOC_PLACEHOLDER_SELECTOR = 'div#toc'
    # this is what we generate (and splits looks for)
    MAIN_TOC_ID = 'main_toc'

    enable_syntax_higlighting = True
    enforce_status_attribute = True
    enforce_lang_attribute = True

    LANG_ATTR = 'lang'
    allowed_langs = ['en', 'en-US', 'it', 'de', 'fr', 'es']

    figure_prefixes = ['fig', 'tab', 'subfig', 'code']
    # cite_prefixes = ['bib']
    div_latex_prefixes = ['exa', 'rem', 'lem', 'def', 'prop', 'prob', 'thm']



Label = namedtuple('Label', 'what number label_self')

Style = namedtuple('Style', 'resets labels')


def get_style_book():
    resets = {
        'part': [],
        'sec': ['sub', 'subsub', 'par'],
        'sub': ['subsub', 'par'],
        'subsub': ['par'],
        'app': ['appsub', 'appsubsub', 'par'],
        'appsub': ['appsubsub', 'par'],
        'appsubsub': ['par'],
        'par': ['subpar'],
        'subpar': [],
        'fig': ['subfig'],
        'subfig': [],
        'tab': [],
        'code': [],
        'exa': [],
        'rem': [],
        'lem': [],
        'def': [],
        'prop': [],
        'prob': [],
        'thm': [],
    }

    labels = {
        'part': Label('Part', '${part}', ''),
        'sec': Label('Chapter', '${sec}', ''),
        'sub': Label('Section', '${sec}.${sub}', ''),
        'subsub': Label('Subsection', '${sec}.${sub}.${subsub}', '${subsub}) '),
        'par': Label('Paragraph', '${par|lower-alpha}', ''),
        'subpar': Label('Sub paragraph', '${subpar|lower-alpha}', ''),
        'app': Label('Appendix', '${app|upper-alpha}', ''),
        'appsub': Label('Section', '${app|upper-alpha}.${appsub}', ''),
        'appsubsub': Label('Subsection', '${app|upper-alpha}.${appsub}.${appsubsub}', ''),
        # global counters
        'fig': Label('Figure', '${fig}', ''),
        'subfig': Label('Figure', '${fig}${subfig|lower-alpha}', '(${subfig|lower-alpha})'),
        'tab': Label('Table', '${tab}', ''),
        'code': Label('Listing', '${code}', ''),
        'rem': Label('Remark', '${rem}', ''),
        'lem': Label('Lemma', '${lem}', ''),
        'def': Label('Definition', '${def}', ''),
        'prob': Label('Problem', '${prob}', ''),
        'prop': Label('Proposition', '${prop}', ''),
        'thm': Label('Theorem', '${thm}', ''),
        'exa': Label('Example', '${exa}', ''),

    }
    return Style(resets, labels)


def get_style_duckietown():
    resets = {
        'part': ['sec'],
        'sec': ['sub', 'subsub', 'par', 'fig', 'tab'],
        'sub': ['subsub', 'par'],
        'subsub': ['par'],
        'app': ['appsub', 'appsubsub', 'par'],
        'appsub': ['appsubsub', 'par'],
        'appsubsub': ['par'],
        'par': ['subpar'],
        'subpar': [],

        'fig': ['subfig'],
        'subfig': [],
        'tab': [],
        'code': [],
        'exa': [],
        'rem': [],
        'lem': [],
        'def': [],
        'prop': [],
        'prob': [],
        'thm': [],
    }

    labels = {
        'part': Label('Part', '${part|upper-alpha}', ''),
        'sec': Label('Unit', '${part|upper-alpha}-${sec}', ''),
        'sub': Label('Section', '${sec}.${sub}', ''),
        'subsub': Label('Subsection', '${sec}.${sub}.${subsub}', '${subsub}) '),
        'par': Label('Paragraph', '${par|lower-alpha}', ''),
        'subpar': Label('Sub paragraph', '${subpar|lower-alpha}', ''),
        'app': Label('Appendix', '${app|upper-alpha}', ''),
        'appsub': Label('Section', '${app|upper-alpha}.${appsub}', ''),
        'appsubsub': Label('Subsection', '${app|upper-alpha}.${appsub}.${appsubsub}', ''),
        # global counters
        'fig': Label('Figure', '${sec}.${fig}', ''),
        'subfig': Label('Figure', '${sec}.${fig}${subfig|lower-alpha}', '(${subfig|lower-alpha})'),
        'tab': Label('Table', '${sec}.${tab}', ''),
        'code': Label('Listing', '${sec}.${code}', ''),
        'rem': Label('Remark', '${rem}', ''),
        'lem': Label('Lemma', '${lem}', ''),
        'def': Label('Definition', '${def}', ''),
        'prob': Label('Problem', '${prob}', ''),
        'prop': Label('Proposition', '${prop}', ''),
        'thm': Label('Theorem', '${thm}', ''),
        'exa': Label('Example', '${exa}', ''),

    }

    return Style(resets, labels)
