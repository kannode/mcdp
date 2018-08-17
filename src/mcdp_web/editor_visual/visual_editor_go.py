# -*- coding: utf-8 -*-
import cgi
import json
from collections import defaultdict, namedtuple

from mcdp import MCDPConstants, logger
from mcdp_dp import WrapAMap, MuxMap
from mcdp_posets import RcompUnits, check_isinstance
from mcdp_report.gdc import GraphDrawingContext
from mcdp_report.gg_ndp import is_special_dp, is_simple_dp, get_best_icon
from mcdp_utils_misc import get_md5
from mcdp_web.editor_fancy import ajax_parse, \
    get_text_from_request2, ajax_error_catch, image_source_from_env, response_data
from mcdp_web.environment import cr2e
from mcdp_web.resource_tree import ResourceThingViewEditorVisual, ResourceThingViewEditorVisual_parse, \
    ResourceThingViewEditorVisual_save, \
    ResourceThingViewEditorVisual_resource
from mcdp_web.utils0 import add_std_vars_context
from mocdp.comp import CompositeNamedDP, SimpleWrap
from mocdp.comp.context import is_fun_node_name, is_res_node_name
from mocdp.ndp import NamedDPCoproduct

Privileges = MCDPConstants.Privileges

ResourceEntry = namedtuple('ResourceEntry', 'mime data')


class ResourcesStorage(object):
    def __init__(self):
        self.data = {}

    def add(self, rid, mime, data):
        self.data[rid] = ResourceEntry(mime, data)

    def get_response_data(self, request, rid):
        entry = self.data[rid]
        return response_data(request, entry.data, entry.mime)

    def store_and_get_url(self, data, mime):
        rid = get_md5(data)
        self.add(rid, mime, data)
        res = 'resource.%s' % rid
        logger.debug('resource: %s' % res)
        return res


class VisualEditor(object):

    def __init__(self):
        # library_name x spec ->  dict(text : ndp)
        # self.last_processed2[library_name x spec][text] = ndp
        self.last_processed2 = defaultdict(lambda: dict())

        self.rs = ResourcesStorage()

    def config(self, config):
        # print('configuring')
        config.add_view(self.view_visual_editor,
                        context=ResourceThingViewEditorVisual,
                        renderer='editor_visual/editor_form_visual.jinja2')
        config.add_view(self.ajax_parse_visual, context=ResourceThingViewEditorVisual_parse, renderer='json')
        config.add_view(self.save, context=ResourceThingViewEditorVisual_save, renderer='json')
        # config.add_view(self.component_image, context=ResourceThingViewEditorVisual_component_image)
        config.add_view(self.serve_resource, context=ResourceThingViewEditorVisual_resource)
        # config.add_view(self.view_new_model_generic, context=ResourceThingsNew, permission=Privileges.WRITE)

    @cr2e
    def serve_resource(self, e):
        rid = e.context.rid
        return self.rs.get_response_data(e.request, rid)

    @cr2e
    def ajax_parse_visual(self, e):
        res = ajax_parse(e, self)
        import mcdp_report.my_gvgen as gvgen
        gg = gvgen.GvGen(options="rankdir=LR;nodesep=0;esep=0")
        parent = None
        yourname = None

        image_source = image_source_from_env(e)
        gdc = GraphDrawingContext(gg, parent, yourname, image_source=image_source)

        if 'thing' in res:
            model = res.pop('thing')
            res['gojs'] = get_gojs_diagram(gdc, self.rs, model)
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


def gojs_node(gdc, rs, name, ndp):
    logger.debug('name: %s %s' % (name, ndp))
    if isinstance(ndp, SimpleWrap):
        return gojs_diagram_simplewrap(gdc, rs, name, ndp)
    elif isinstance(ndp, NamedDPCoproduct):
        return gojs_diagram_coproduct(gdc, rs, name, ndp)
    else:
        return gojs_node_generic(gdc, rs, name, ndp)


def gojs_diagram_simplewrap(gdc, rs, name, ndp):
    logger.debug('gojs_diagram_simplewrap: %s %s' % (name, ndp))
    is_special = is_special_dp(ndp.dp)
    is_simple = is_simple_dp(ndp.dp)
    best_icon = get_best_icon(gdc, ndp)

    logger.debug('is_special: %s  is_simple: %s' % (is_special, is_simple))
    if is_simple:
        label = type(ndp.dp).__name__

        if isinstance(ndp.dp, WrapAMap):
            label = ndp.dp.diagram_label()

            if isinstance(ndp.dp.amap, MuxMap):
                label = 'Mux(%s)' % ndp.dp.amap.coords

        # sname = 'simple'
        res = gojs_node_generic(gdc, rs, name, ndp)

        res['name'] = label
        res['category'] = 'simple'
        logger.debug('label %r' % label)
        return res

    if is_special:
        res = gojs_node_generic(gdc, rs, name, ndp)
        res['name'] = None
        data = open(best_icon).read()
        res['source'] = rs.store_and_get_url(data, 'png')
        res['category'] = 'special'
        return res
        #
        # gdc.styleAppend(sname, 'image', best_icon)
        # gdc.styleAppend(sname, 'imagescale', 'true')
        # gdc.styleAppend(sname, 'fixedsize', 'true')
        #
        # rel_to_8 = MCDPConstants.diagrams_fontsize / 8
        # diagrams_smallimagesize = MCDPConstants.diagrams_smallimagesize_rel * \
        #                           rel_to_8
        # # diagrams_leqimagesize = 0.2 * rel_to_8
        #
        # gdc.styleAppend(sname, 'height', diagrams_smallimagesize)
        # gdc.styleAppend(sname, "shape", "none")
        # label = ''

    if best_icon is not None:
        if gdc.yourname is not None:
            if len(gdc.yourname) >= 1 and gdc.yourname[0] == '_':
                shortlabel = ""
            else:
                shortlabel = gdc.yourname
        else:
            # mcdp_dev_warning('double check this (sep 16)')
            # shortlabel = classname
            shortlabel = None

        # # shortlabel = '<I><B>%sa</B></I>' % shortlabel
        # sname = classname
        # gdc.styleAppend(sname, 'imagescale', 'true')
        # #                 gdc.styleAppend(sname, 'height', MCDPConstants.diagrams_bigimagesize)
        # gdc.styleAppend(sname, "shape", "box")
        # gdc.styleAppend(sname, "style", "rounded")
        # #                 label = ("<TABLE CELLBORDER='0' BORDER='0'><TR><TD>%s</TD></TR>"
        # #                 "<TR><TD'><IMG SRC='%s' SCALE='TRUE'/></TD></TR></TABLE>")
        # # these work as max size
        # rel_to_8 = MCDPConstants.diagrams_fontsize / 8
        # diagrams_bigimagesize = MCDPConstants.diagrams_bigimagesize_rel * \
        #                         rel_to_8  # points
        #
        # width = diagrams_bigimagesize
        # ratio = 0.8
        # height = diagrams_bigimagesize * ratio
        # label = ("<TABLE CELLBORDER='0' BORDER='0'><TR><TD>%s</TD></TR>"
        #          "<TR><TD fixedsize='true' width='%d' height='%d'><IMG SRC='%s'/></TD></TR></TABLE>")
        #
        if shortlabel is None:
            shortlabel = ''
        # label %= shortlabel, width, height, best_icon

        res = gojs_node_generic(gdc, rs, name, ndp)
        res['name'] = shortlabel

        res['category'] = ''
        return res

    res = gojs_node_generic(gdc, rs, name, ndp)

    return res


def gojs_diagram_coproduct(gdc, rs, name, ndp):
    raise NotImplementedError()


def get_gojs_diagram(gdc, rs, model):
    check_isinstance(model, CompositeNamedDP)

    gojs = {}
    gojs['nodes'] = nodes = []

    for name, ndp in model.get_name2ndp().items():
        it_is, fname = is_fun_node_name(name)
        if it_is:
            node = gojs_node_fun(gdc, rs, name, ndp)
            nodes.append(node)
            continue

        it_is, rname = is_res_node_name(name)
        if it_is:
            node = gojs_node_res(gdc, rs, name, ndp)
            nodes.append(node)
            continue

        node = gojs_node(gdc, rs, name, ndp)
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


def gojs_node_fun(gdc, rs, name, ndp):
    node = gojs_node_generic(gdc, rs, name, ndp)
    node['category'] = 'f_template'
    return node


def gojs_node_res(gdc, rs, name, ndp):
    node = gojs_node_generic(gdc, rs, name, ndp)
    node['category'] = 'r_template'
    return node


def get_type_label(T):
    if isinstance(T, RcompUnits):
        return T.string
    else:
        return str(T)


def gojs_node_generic(gdc, rs, name, ndp):
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
