# -*- coding: utf-8 -*-
import cgi
import json
from collections import defaultdict

from mocdp.comp.context import is_fun_node_name, is_res_node_name

from mcdp import MCDPConstants
from mcdp_posets import RcompUnits
from mcdp_web.editor_fancy import ajax_parse, \
    get_text_from_request2, ajax_error_catch
from mcdp_web.environment import cr2e
from mcdp_web.resource_tree import ResourceThingViewEditorVisual, ResourceThingViewEditorVisual_parse, \
    ResourceThingViewEditorVisual_save
from mcdp_web.utils0 import add_std_vars_context
from mocdp.comp import CompositeNamedDP

Privileges = MCDPConstants.Privileges


class VisualEditor(object):

    def __init__(self):
        # library_name x spec ->  dict(text : ndp)
        # self.last_processed2[library_name x spec][text] = ndp
        self.last_processed2 = defaultdict(lambda: dict())

    def config(self, config):
        # print('configuring')
        config.add_view(self.view_visual_editor,
                        context=ResourceThingViewEditorVisual,
                        renderer='editor_visual/editor_form_visual.jinja2')
        config.add_view(self.ajax_parse_visual, context=ResourceThingViewEditorVisual_parse, renderer='json')
        config.add_view(self.save, context=ResourceThingViewEditorVisual_save, renderer='json')
        # config.add_view(self.graph_generic, context=ResourceThingViewEditorGraph)
        # config.add_view(self.view_new_model_generic, context=ResourceThingsNew, permission=Privileges.WRITE)

    @cr2e
    def ajax_parse_visual(self, e):
        res = ajax_parse(e, self)

        if 'thing' in res:
            model = res.pop('thing')
            res['gojs'] = add_gojs_diagram_info(model)
        else:
            res['gojs'] = None

        return res

    @add_std_vars_context
    @cr2e
    def view_visual_editor(self, e):
        source_code = e.thing
        nrows = int(len(source_code.split('\n')) + 6)
        nrows = min(nrows, 25)

        source_code = cgi.escape(source_code)
        res = {
            'source_code': unicode(source_code, 'utf-8'),
            'source_code_json': unicode(json.dumps(source_code), 'utf-8'),
            'rows': nrows,
            'ajax_parse': e.spec.url_part + '_ajax_parse',
            'error': None,
            'url_part': e.spec.url_part,
        }
        return res

    @cr2e
    def save(self, e):
        string = get_text_from_request2(e.request)

        def go():
            db_view = e.app.hi.db_view
            library = db_view.repos[e.repo_name].shelves[e.shelf_name].libraries[e.library_name]
            things = library.things.child(e.spec_name)
            things[e.thing_name] = string
            return {'ok': True, 'saved_string': string}

        return ajax_error_catch(go, environment=e)
    #
    # @cr2e
    # def ajax_parse(self, e):
    #     string = get_text_from_request2(e.request)
    #     text = e.request.json_body['text'].encode('utf8')
    #     req = {'text': e.request.json_body['text']}
    #     text_hash = get_sha1(text)
    #     key = (e.library_name, e.spec.url_part, e.thing_name, text_hash)
    #
    #     cache = self.last_processed2
    #
    #     make_relative = lambda s: self.make_relative(e.request, s)
    #     library = library_from_env(e)
    #
    #     def go():
    #         with timeit_wall('process_parse_request'):
    #             res = process_parse_request(library, string, e.spec, key, cache, make_relative)
    #         res['request'] = req
    #         return res
    #
    #     return ajax_error_catch(go, environment=e)
    #
    # @add_std_vars_context
    # @cr2e
    # def view_edit_form_fancy(self, e):
    #     source_code = e.thing
    #     nrows = int(len(source_code.split('\n')) + 6)
    #     nrows = min(nrows, 25)
    #
    #     source_code = cgi.escape(source_code)
    #     res = {
    #         'source_code': unicode(source_code, 'utf-8'),
    #         'source_code_json': unicode(json.dumps(source_code), 'utf-8'),
    #         #             'realpath': realpath,
    #         'rows': nrows,
    #         'ajax_parse': e.spec.url_part + '_ajax_parse',
    #         'error': None,
    #         'url_part': e.spec.url_part,
    #     }
    #     return res
    #
    # @cr2e
    # def graph_generic(self, e):
    #     data_format = e.context.data_format
    #     text_hash = e.context.text_hash
    #
    #     def go():
    #         image_source = image_source_from_env(e)
    #         library = library_from_env(e)
    #
    #         with timeit_wall('graph_generic', 1.0):
    #             key = (e.library_name, e.spec.url_part, e.thing_name, text_hash)
    #
    #             if not key in self.last_processed2:
    #                 logger.error('Cannot find key %s' % str(key))
    #                 logger.error('keys: %s' % list(self.last_processed2))
    #                 context = e.library._generate_context_with_hooks()
    #                 thing = e.spec.load(e.library, e.thing_name, context=context)
    #             else:
    #                 thing = self.last_processed2[key]
    #                 if thing is None:
    #                     return response_image(e.request, 'Could not parse.')
    #
    #             with timeit_wall('graph_generic - get_png_data', 1.0):
    #                 data = e.spec.get_png_data(image_source=image_source,
    #                                            name=e.thing_name,
    #                                            thing=thing,
    #                                            data_format=data_format,
    #                                            library=library)
    #             mime = get_mime_for_format(data_format)
    #             return response_data(e.request, data, mime)
    #
    #     return self.png_error_catch2(e.request, go)
    #
    # @cr2e
    # def view_new_model_generic(self, e):
    #     new_thing_name = e.context.name
    #     logger.info('Creating new %r' % new_thing_name)
    #
    #     basename = '%s.%s' % (new_thing_name, e.spec.extension)
    #     url_edit = '../%s/views/edit_fancy/' % new_thing_name
    #
    #     if new_thing_name in e.things:
    #         error = 'File %r already exists.' % basename
    #         template = 'editor_fancy/error_model_exists_generic.jinja2'
    #         res = {'error': error, 'url_edit': url_edit,
    #                'widget_name': new_thing_name, 'root': e.root,
    #                'static': 'XXX'}  # XXX
    #         e.request.response.status = 409  # Conflict
    #         return render_to_response(template, res, request=e.request, response=e.request.response)
    #     else:
    #         source = e.spec.minimal_source_code
    #         e.things[new_thing_name] = source
    #         raise HTTPFound(url_edit)
    #


def add_gojs_diagram_info(model):
    gojs = {}
    gojs['nodes'] = nodes = []

    assert isinstance(model, CompositeNamedDP)

    for name, ndp in model.get_name2ndp().items():
        it_is, fname = is_fun_node_name(name)
        if it_is:
            node = gojs_node_fun(name, ndp)
            nodes.append(node)
            continue

        it_is, rname = is_res_node_name(name)
        if it_is:
            node = gojs_node_res(name, ndp)
            nodes.append(node)
            continue

        node = gojs_node(name, ndp)
        nodes.append(node)

    links = []
    for c in model.get_connections():
        link = {'from': c.dp1, 'fromPort': c.s1, 'to': c.dp2, 'toPort': c.s2}
        if is_fun_node_name(c.dp1)[0]:
            link['category'] = 'f_link'
        if is_res_node_name(c.dp2)[0]:
            link['category'] = 'r_link'

        links.append(link)

    gojs['links'] = links

    return gojs


def gojs_node_fun(name, ndp):
    node = gojs_node(name, ndp)
    node['category'] = 'f_template'
    return node


def gojs_node_res(name, ndp):
    node = gojs_node(name, ndp)
    node['category'] = 'r_template'
    return node


def get_type_label(T):
    if isinstance(T, RcompUnits):
        return T.string
    else:
        return str(T)


def gojs_node(name, ndp):
    functions = []
    for fname in ndp.get_fnames():

        ftype = ndp.get_ftype(fname)
        fport = {'portId': fname, 'port_label': "%s [%s]" % (fname, get_type_label(ftype)),
                 'unit': str(ftype)}
        functions.append(fport)

    resources = []

    for rname in ndp.get_rnames():
        rtype = ndp.get_rtype(rname)
        rport = {'portId': rname, 'port_label': "%s [%s]" % (rname, get_type_label(rtype)),
                 'unit': str(rtype)}
        resources.append(rport)

    node = {'key': name, "name": name, "leftArray": functions,
            "rightArray": resources}

    return node

    #
    # {
    #
    # //         key: 1, group: 0, "name": "unit One", "loc": "101 204",
    # //         "leftArray": [
    # //             {
    # //                 "portId": "F0",
    # //                 "port_label": "F0 [m]",
    # //                 "unit": "m",
    # //             }
    # //         ],
    # //
    # //         "rightArray": [
    # //             {
    # //                 "portId": "R0",
    # //                 "port_label": "R0 [W]",
    # //                 "unit": "W",
    # //             },
    # //             {
    # //
    # //                 "portId": "R1",
    # //                 "port_label": "R1 [m]",
    # //                 "unit": "m",
    # //             }]
    # //     },
