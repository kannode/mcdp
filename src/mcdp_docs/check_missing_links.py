from mocdp import logger
from bs4.element import Comment, Tag
from mcdp_web.renderdoc.highlight import add_class

def get_id2element(soup):
    id2element = {}
    duplicates = set()
    
    # ignore the maths
    ignore = set() 
    for element in soup.select('svg [id]'): # node with ID below SVG
        ignore.add(element['id'])
    for element in soup.select('svg[id]'): # svg with ID
        ignore.add(element['id'])
    for element in soup.select('[id^="MathJax"]'): # stuff created by MathJax
        ignore.add(element['id'])
        
    
    for element in soup.select('[id]'):
        ID = element['id']
        if ID in ignore:
            continue
        if ID in id2element:
            duplicates.add(ID)
            other = id2element[ID]
            msg = 'More than one element with id %r.' % ID
#             msg += str(other)
            logger.error(msg)
            for e0 in [element, other]:
                if not 'errored' in e0.attrs.get('class', ''):
                    msg =  'Duplicated ID %r' % element['id']
                    logger.error(msg)
                    add_class(e0, 'errored')
                    w = Tag(name='span', attrs={'class':'duplicated-id'})
                    w.string =msg
                    e0.insert_after(w)
        id2element[element['id']] = element  
    return id2element, duplicates

def check_if_any_href_is_invalid(soup):
    errors = []
    math_errors = []
    
    # let's first find all the IDs
    id2element, duplicates = get_id2element(soup)
    
    
    for a in soup.select('a[href^="#"]'):
        href = a['href']
        if a.has_attr('class') and  "mjx-svg-href" in a['class']:
            msg = 'Invalid math reference (sorry, no details).'
            logger.error(msg)
            a.insert_before(Comment('Error: %s' % msg))
            math_errors.append(msg)
            continue 

        assert href.startswith('#')
        ID = href[1:]
        if not ID in id2element:
            # try to fix it
            # if there is already a prefix, remove it 
            if ':' in href:
                i = href.index(':')
                core = href[i+1:]
            else:
                core = ID
            possible = ['sec', 'sub', 'subsub', 'fig', 'tab', 'code',
                        'def', 'eq', 'rem', 'lem', 'prob', 'prop', 'exa', 'thm' ]
            matches = [] 
            others = []
            for possible_prefix in possible:
                why_not = possible_prefix + ':' + core
                others.append(why_not)
                if why_not in id2element:
                    matches.append(why_not)
            
            if len(matches) > 1:
                msg = '%s not found, and multiple matches for heuristics (%s)' % (href, matches)
                logger.error(msg)
                add_class(a, 'errored')
                w = Tag(name='span', attrs={'class':'href-invalid href-invalid-missing'})
                w.string = msg
                a.insert_after(w)
            elif len(matches) == 1:
                msg = '%s not found, but corrected in %s' % (href, matches[0])
                logger.debug(msg)
                
                add_class(a, 'warning')
                w = Tag(name='span', attrs={'class':'href-replaced'})
                w.string = msg
                a['href'] = '#' + matches[0]
                a.insert_after(w)
                
            else:
                msg = 'Not found %r' % (href)
#                 msg = 'Not found %r (also tried %s)' % (href, ", ".join(others))
                logger.error(msg)
                errors.append(msg)
                if not 'errored' in a.attrs.get('class', ''):
                    add_class(a, 'errored')
                    w = Tag(name='span', attrs={'class':'href-invalid href-invalid-missing'})
                    w.string = msg
                    a.insert_after(w)
            
        if ID in duplicates:
            msg = 'More than one element matching %r.' % href
            logger.error(msg)
            if not 'errored' in a.attrs.get('class', ''):
                add_class(a, 'errored')
                w = Tag(name='span', attrs={'class':'href-invalid href-invalid-multiple'})
                w.string = msg
                a.insert_after(w)

            errors.append(msg)
            
    return errors, math_errors