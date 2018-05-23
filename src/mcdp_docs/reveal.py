from bs4 import Tag
from mcdp_utils_xml import bs, copy_contents_into, copy_contents_into_beginning


def create_reveal(soup, res):

    head = soup.find('head')

    header = """
        <link rel="stylesheet" href="revealjs/css/reveal.css">
    	
    """

    copy_contents_into_beginning(bs(header), head)

    # language=html
    footer = """
        <script src="revealjs/lib/js/head.min.js"></script>
        <script src="revealjs/js/reveal.js"></script>
		<script>
        options = {
            transition: 'none',
            center: false,
        	dependencies: [
        		{ src: 'revealjs/plugin/notes/notes.js', async: true }
        	],
        	// The "normal" size of the presentation, aspect ratio will be preserved
            // when the presentation is scaled to fit different resolutions. Can be
            // specified using percentage units.
            width: 960,
            height: 700,

            // Factor of the display size that should remain empty around the content
            margin: 0.1,
        };
        Reveal.initialize(options);
		</script>
	"""

    assert isinstance(soup, Tag)
    body = soup.find('body')
    copy_contents_into(bs(footer), body)

    """
    <section class="without-header-inside" level="book">

    <section class="without-header-inside" level="part">

    """

    s1 = body.find('section', attrs=dict(level="book"))
    s1.name = 'div'
    s1.attrs['class']='reveal'

    s2 = body.find('section', attrs=dict(level="part"))
    s2.name = 'div'
    s2.attrs['class'] = 'slides'
