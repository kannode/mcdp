from bs4.element import Tag, NavigableString

from mcdp.exceptions import DPSyntaxError
from mcdp_lang_utils import Where, location
from mcdp_utils_xml import add_class


def other_abbrevs(soup):
    """
        v, val, value   --> mcdp-value
           pos, poset   --> mcdp-poset
           
        <val>x</val> -> <mcdp-value></mcdp-value>
        <pos>x</pos> -> <mcdp-poset></mcdp-poset>
        
        <s> (strikeout!) -> <span> 
        
        <p>TODO:...</p> -> <div class="todo"><p><span>TODO:</span></p>
    """ 
    from .task_markers import substitute_task_markers
   
    other_abbrevs_mcdps(soup)
#     other_abbrevs_envs(soup)
    
    substitute_task_markers(soup)
    substitute_special_paragraphs(soup)
    
def other_abbrevs_mcdps(soup):
    translate = {
        'v': 'mcdp-value',
        'val': 'mcdp-value',
        'value': 'mcdp-value',
        'pos': 'mcdp-poset',
        'poset': 'mcdp-poset',
        's': 'span',
        
    }
    for k, v in translate.items():
        for e in soup.select(k):
            e.name = v
#             
# def other_abbrevs_envs(soup):
#     # This is not used yet
#     translate = { 
#         'knowledge-graph': ('div', {'markdown':1, 'class':'requirements'}),
#         'example-usage': ('div', {'markdown':1, 'class':'example-usage'}),
#         'comment': ('div', {'markdown':1, 'class':'comment'}),
#         'question': ('div', {'markdown':1, 'class':'question'}),
#         'doubt': ('div', {'markdown':1, 'class':'doubt'}),
#     }
#     for oname, (name, attrs) in translate.items():
#         for e in soup.select(oname):
#             e.name = name
#             for k, v in attrs.items():
#                 if not k in e.attrs:
#                     e.attrs[k] = v
                    
    
prefix2class = {
    'TODO: ': 'todo',
    'TOWRITE: ': 'special-par-towrite',  
    'Task: ': 'special-par-task',
    'Remark: ': 'special-par-remark',  
    'Note: ': 'special-par-note',
    'Symptom: ': 'special-par-symptom',
    'Resolution: ': 'special-par-resolution',
    'Bad:': 'special-par-bad',
    'Better:': 'special-par-better',
    'Warning:': 'special-par-warning',
    'Q:': 'special-par-question',
    'A:': 'special-par-answer',
    "Assigned: ": 'special-par-assigned',
    "Author: ": 'special-par-author',
    "Maintainer: ": 'special-par-maintainer',
    "Point of contact: ": 'special-par-point-of-contact',
    "Slack channel: ": 'special-par-slack-channel',
    # Reference and See are the same thing
    'See: ': 'special-par-see',
    'Reference: ': 'special-par-see',
    'Requires: ': 'special-par-requires',
    'Results: ': 'special-par-results',
    'Result: ': 'special-par-results',
    'Next steps: ': 'special-par-next',
    'Next Steps: ': 'special-par-next',
    'Next: ': 'special-par-next',
    'Motto: ': 'special-par-motto',
    'Recommended: ': 'special-par-recommended',
    'See also: ': 'special-par-see-also',
    
    'Comment: ': 'comment',
    'Question: ': 'question',
    'Doubt: ': 'doubt',
} 

def has_special_line_prefix(line):
    for prefix in prefix2class:
        if line.startswith(prefix):
            return prefix
    return None

def check_good_use_of_special_paragraphs(md, filename):
    lines = md.split('\n')
    for i in range(1, len(lines)):
        line = lines[i]
        prev = lines[i-1]
        
        prefix = has_special_line_prefix(line)        
        if prefix:
            if prev.strip():
                msg = ('Wrong use of special paragraph indicator. You have '
                       'to leave an empty line before the special paragraph.')
                c  = location(i, 1, md)
                c_end = c + len(prefix)
                where = Where(md, c, c_end).with_filename(filename)
                raise DPSyntaxError(msg, where=where)

        if False:
            def looks_like_list_item(s):
                if s.startswith('--'):
                    return False
                if s.startswith('**'):
                    return False
                return s.startswith('-') or s.startswith('*')
            
            if looks_like_list_item(line):
                if prev.strip() and not looks_like_list_item(prev):
                    msg = ('Wrong use of list indicator. You have '
                           'to leave an empty line before the list.')
                    c  = location(i, 1, md)
                    c_end = c + 1
                    where = Where(md, c, c_end).with_filename(filename)
                    raise DPSyntaxError(msg, where=where)
                
                

def substitute_special_paragraphs(soup):
    
    
    for prefix, klass in prefix2class.items():
        substitute_special_paragraph(soup, prefix, klass)
        
    make_details = ['comment', 'question', 'doubt']
    for c in make_details:
        for e in list(soup.select('.%s' % c)):
            details = Tag(name='details')
            add_class(details, c)
            summary = Tag(name='summary')
            summary.append(c)
            details.append(summary)
            rest = e.__copy__()
            details.append(rest)
            e.replace_with(details)
            
#             e.append('Found')
        
def substitute_special_paragraph(soup, prefix, klass):
    """ 
        Looks for paragraphs that start with a simple string with the given prefix. 
    
        From:
        
            <p>prefix contents</p>
            
        Creates:
        
            <div class='klass-wrap'><p class='klass'>contents</p></div>
    """
    ps = list(soup.select('p'))
    for p in ps:
        # Get first child
        contents = list(p.contents)
        if not contents:
            continue
        c = contents[0]
        if not isinstance(c, NavigableString):
            continue

        s = c.string
        starts = s.lower().startswith(prefix.lower())
        if not starts: 
            continue

        without = s[len(prefix):]
        ns = NavigableString(without)
        c.replaceWith(ns)
    
        div = Tag(name='div')
        add_class(div, klass + '-wrap')
        add_class(p, klass)
        parent = p.parent
        i = parent.index(p)
        p.extract()
        div.append(p)
        parent.insert(i, div)

