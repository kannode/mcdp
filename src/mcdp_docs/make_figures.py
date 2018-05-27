# -*- coding: utf-8 -*-
from bs4.element import NavigableString, Tag
from mcdp_docs.location import HTMLIDLocation

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


    for figure in soup.select('figure[id]'):
        ID = 'fig:' + figure.attrs['id']
        go(soup, figure, ID, res, location)

    for towrap in soup.select('[figure-id]'):
        ID = towrap.attrs['figure-id']
        go(soup, towrap, ID, res, location)



def go(soup, towrap, ID, res, location):
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

    if 'caption-left' in towrap.attrs.get('figure-class', ''):
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
    if towrap.has_attr('figure-class'):
        for k in towrap['figure-class'].split(' '):
            #                 logger.debug('figure-class: %s' % k)
            add_class(towrap, k)
            ## XXX but not to figure itself?
            add_class(fig, k)
            add_class(outside, k)

    i = parent.index(towrap)
    towrap.extract()
    figcontent = Tag(name='div', attrs={'class': 'figcontent'})
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
