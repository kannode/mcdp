# -*- coding: utf-8 -*-
from bs4.element import NavigableString, Tag
from mcdp_docs.tocs import add_id_if_not_present

from mcdp_docs.location import HTMLIDLocation
from mcdp_utils_xml import get_parents_names

from .logs import logger


def make_figure_from_figureid_attr(soup, res, location):
    """
        Makes a figure:
            <e figure-id='fig:ure' figure-caption='ciao'/> 
                    
        <figure id="fig:ure">
            <e figure-id='fig:ure' figure-caption='ciao'/>
            <figcaption>ciao</figcaption>
            
            <div style='clear: both;'></div> <!-- for floating stuff-->
        </figure>

        Makes a table:
            <e figure-id='tab:ure' figure-caption='ciao'/>
            
        becomes
        
        
        figure-id
        figure-class

        
    """


    for figure in list(soup.select('figure')):
        if not 'id' in figure.attrs:
            add_id_if_not_present(figure)

        names = get_parents_names(figure)
        if 'figure' in names:
            prefix = 'subfig:'
        else:
            prefix = 'fig:'

        ID0 = figure.attrs['id']
        if not 'fig:' in ID0:
            ID = prefix + ID0
        else:
            ID = ID0

        figure_class = figure.attrs.get('class', '')
        go(soup, figure, ID, figure_class, res, location)

    for towrap in soup.select('[figure-id]'):
        ID = towrap.attrs['figure-id']
        figure_class = towrap.attrs.get('figure-class', [])
        go(soup, towrap, ID, figure_class, res, location)



def go(soup, towrap, ID, figure_class, res, location):
    from mcdp_docs.highlight import add_class
    parent = towrap.parent
    fig = Tag(name='figure')
    fig['id'] = ID
    caption_below = True
    if ID.startswith('fig:'):
        add_class(fig, 'figure')
    elif ID.startswith('subfig:'):
        add_class(fig, 'subfloat')
    elif ID.startswith('tab:'):
        add_class(fig, 'table')
        caption_below = False
    elif ID.startswith('code:'):
        add_class(fig, 'code')
        pass
    else:
        msg = 'The ID %r should start with fig: or tab: or code:' % ID
        res.note_error(msg, locations=HTMLIDLocation.for_element(towrap, location))
        return

    if 'caption-left' in figure_class:
        caption_below = False
    external_caption_id = '%s:caption' % ID
    external_caption = soup.find(id=external_caption_id)
    if external_caption is None:
        external_caption = towrap.find(name='figcaption')

    if external_caption is not None:
        #             print('using external caption %s' % str(external_caption))
        external_caption.extract()
        if external_caption.name != 'figcaption':
            logger.error('Element %s#%r should have name figcaption.' %
                         (external_caption.name, external_caption_id))
            external_caption.name = 'figcaption'
        figcaption = external_caption

        if towrap.has_attr('figure-caption'):
            msg = 'Already using external caption for %s' % ID
            res.note_error(msg, location=HTMLIDLocation.for_element(towrap, location))
            return

    else:
        #             print('could not find external caption %s' % external_caption_id)
        if towrap.has_attr('figure-caption'):
            caption = towrap['figure-caption']
        else:
            caption = ''
        figcaption = Tag(name='figcaption')
        figcaption.append(NavigableString(caption))

    outside = Tag(name='div')
    outside['id'] = ID + '-wrap'
    if towrap.has_attr('figure-style'):
        outside['style'] = towrap['figure-style']

    for k in figure_class:
        #                 logger.debug('figure-class: %s' % k)
        add_class(towrap, k)
        ## XXX but not to figure itself?
        add_class(fig, k)
        add_class(outside, k)

    i = parent.index(towrap)
    towrap.extract()
    figcontent = Tag(name='div', attrs={'class': 'figcontent'})
    if towrap.name == 'figure':
        towrap.name = 'div'
        add_class(towrap, 'figure-conv-to-div')
    figcontent.append(towrap)

    #         <div style='clear: both;'></div> <!-- for floating stuff-->

    # Not 100% where it should go
    breaking_div = Tag(name='div')
    breaking_div.attrs['style'] = 'clear: both'
    figcontent.append(breaking_div)

    fig.append(figcontent)

    if caption_below:
        fig.append(figcaption)
    else:
        fig.insert(0, figcaption)

    add_class(outside, 'generated-figure-wrap')
    add_class(fig, 'generated-figure')
    outside.append(fig)

    parent.insert(i, outside)
