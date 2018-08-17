# -*- coding: utf-8 -*-
import cgi
import json
from collections import defaultdict

from mcdp_web.editor_fancy import AppEditorFancyGeneric, ResourceThingViewEditorParse, ajax_parse, \
    get_text_from_request2, ajax_error_catch

from mcdp import MCDPConstants
from mcdp_web.environment import cr2e
from mcdp_web.resource_tree import ResourceThingViewEditorVisual, ResourceThingViewEditorVisual_parse, \
    ResourceThingViewEditorVisual_save
from mcdp_web.utils0 import add_std_vars_context

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
        config.add_view(self.ajax_parse, context=ResourceThingViewEditorVisual_parse, renderer='json')
        config.add_view(self.save, context=ResourceThingViewEditorVisual_save, renderer='json')
        # config.add_view(self.graph_generic, context=ResourceThingViewEditorGraph)
        # config.add_view(self.view_new_model_generic, context=ResourceThingsNew, permission=Privileges.WRITE)

    @cr2e
    def ajax_parse(self, e):
        return ajax_parse(e, self)

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
