from bs4 import Tag
from mcdp_utils_xml import bs, copy_contents_into


def create_reveal(soup, res):

    head = soup.find('head')

    header = """
        <link rel="stylesheet" href="revealjs/css/reveal.css">
    	<link rel="stylesheet" href="revealjs/css/theme/white.css">
    """

    copy_contents_into(bs(header), head)

    footer = """
        <script src="revealjs/lib/js/head.min.js"></script>
        <script src="revealjs/js/reveal.js"></script>
		<script>
        options = {
            transition: 'none',
        	dependencies: [
        		{ src: 'revealjs/plugin/notes/notes.js', async: true }
        	]
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
