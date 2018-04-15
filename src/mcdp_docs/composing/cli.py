import copy

from bs4.element import Tag
from contracts import contract
from contracts.utils import check_isinstance, raise_wrapped
import yaml

from decent_params.utils.script_utils import UserError
from mcdp import logger
from mcdp_docs.add_edit_links import add_github_links_if_edit_url
from mcdp_docs.composing.recipes import Recipe, RecipeContext, append_all
from mcdp_docs.manual_constants import MCDPManualConstants
from mcdp_docs.manual_join_imp import generate_and_add_toc, \
    document_final_pass_after_toc
from mcdp_docs.tocs import get_ids_from_soup, is_empty_link
from mcdp_utils_misc import write_data_to_file
from mcdp_utils_xml import add_class, get_classes, bs_entire_document
from quickapp import QuickAppBase


class ComposeConfig(object):
    @contract(recipe=Recipe, input_=str, output=str)
    def __init__(self, recipe, input_, output, purl_prefix, remove_status, show_removed):
        check_isinstance(output, str)
        check_isinstance(input_, str)
        self.recipe = recipe
        self.input = input_
        self.output = output
        self.purl_prefix = purl_prefix
        self.remove_status = remove_status
        self.show_removed = show_removed

    @staticmethod
    def from_yaml(data):
        """
            input:
            recipe:
            output:
        """
        check_isinstance(data, dict)
        data = copy.deepcopy(data)

        input_ = data.pop('input')
        output = data.pop('output')
        recipe = data.pop('recipe')
        purl_prefix = data.pop('purl_prefix')
        remove_status = data.pop('remove_status', [])
        show_removed = data.pop('show_removed', True)
        if not isinstance(remove_status, list):
            msg = 'I expected that remove_status was a list; found %r.' % remove_status
            raise ValueError(msg)

        recipe = Recipe.from_yaml(recipe)

        if data:
            msg = 'Spurious fields %s' % list(data)
            raise ValueError(msg)

        return ComposeConfig(recipe, input_, output, purl_prefix, remove_status, show_removed)


class Compose(QuickAppBase):
    """ """

    def define_program_options(self, params):
        params.add_string('config', help="""Configuration file""")

    def go(self):
        options = self.get_options()
        config = options.config
        try:
            data = yaml.load(open(config).read())
            compose_config = ComposeConfig.from_yaml(data)
        except ValueError as e:
            msg = 'Cannot read YAML config file %s' % config
            raise_wrapped(UserError, e, msg, compact=True)
        compose_go(compose_config)


compose_main = Compose.get_sys_main()


def compose_go(compose_config):
    input_ = compose_config.input
    output = compose_config.output
    recipe = compose_config.recipe
    permalink_prefix = compose_config.purl_prefix

    # Read input file
    logger.info('Reading %s' % input_)
    data = open(input_).read()
    soup = bs_entire_document(data)
    # Create context
    doc = soup.__copy__()
    body = Tag(name='body')
    doc.body.replace_with(body)
    elements = recipe.make(RecipeContext(soup=soup))
    check_isinstance(elements, list)
    append_all(body, elements)

    # Now remove stuff
    for status in compose_config.remove_status:
        removed = []
        for section in list(body.select('section[status=%s]' % status)):
            level = section.attrs['level']
            if not level in ['sec', 'part']:
                continue

            section_id = section.attrs['id']
            pure_id = section_id.replace(':section', '')
            removed.append(section.attrs['id'])

            if compose_config.show_removed:
                # remove everything that is not a header
                keep = ['h1', 'h2', 'h3', 'h4', 'h5']
                for e in list(section.children):
                    if e.name not in keep:
                        e.extract()
                    else:
                        e.append(' [%s]' % status)

                p = Tag(name='p')
                p.append("This section has been removed because it is in status %r. " % status)
                a = Tag(name='a')
                a.attrs['href'] = 'http://purl.org/dt/master/%s' % pure_id
                a.append("If you are feeling adventurous, you can read it on master.")
                p.append(a)

                section.append(p)

                p = Tag(name='p')
                p.append("To disable this behavior, and completely hide the sections, ")
                p.append("set the parameter show_removed to false in fall2017.version.yaml.")
                section.append(p)
            else:
                section.extract()

        #             section.replace_with(div)

        if not removed:
            logger.info('Found no section with status = %r to remove.' % status)
        else:
            logger.info('I removed %d sections with status %r.' % (len(removed), status))
            logger.debug('Removed: %s' % ", ".join(removed))

    add_github_links_if_edit_url(doc, permalink_prefix=permalink_prefix)

    generate_and_add_toc(doc)
    doc = doc.__copy__()

    #     generate_and_add_toc(soup)
    #     substituting_empty_links(soup)
    raise_errors = False
    find_links_from_master(master_soup=soup, version_soup=doc, raise_errors=raise_errors)

    document_final_pass_after_toc(doc)
    results = str(doc)
    write_data_to_file(results, output)


def find_links_from_master(master_soup, version_soup, raise_errors):
    logger.info('find_links_from_master')
    from mcdp_docs.tocs import sub_link
    # find all ids
    master_ids = get_ids_from_soup(master_soup)
    version_ids = get_ids_from_soup(version_soup)
    missing = []
    seen = []
    found = []
    for a, eid in a_linking_to_fragments(version_soup):
        seen.append(eid)

        if eid not in version_ids:
            missing.append(eid)
            if eid in master_ids:
                #                 logger.info('found %s in master' % eid)
                found.append(eid)
                linked_element = master_ids[eid]
                if is_empty_link(a):
                    #                     logger.debug('is: %s' % a)
                    if not get_classes(a):
                        add_class(a, MCDPManualConstants.CLASS_ONLY_NAME)
                    #                     logger.debug('is before: %s' % a)
                    sub_link(a, eid, linked_element, raise_errors)
                #                     logger.debug('is now: %s' % a)

                href = 'http://purl.org/dth/%s' % remove_prefix(eid)

                a.attrs['href'] = href
                add_class(a, 'link-to-master')
            else:
                logger.info('Not found %r in master.' % eid)


def a_linking_to_fragments(soup):
    for a in soup.select('a'):
        href = a.attrs['href']
        if not href.startswith('#'):
            continue
        eid = href[1:]
        yield a, eid


def remove_prefix(id_):
    if ':' in id_:
        return id_[id_.index(':') + 1:]
    else:
        return id_
