from collections import OrderedDict
import logging
import os

from compmake.plugins.console_banners import name
from contracts import contract
from contracts.utils import indent
from mcdp.logs import logger
from mcdp_cli.utils_wildcard import expand_string
from mcdp_docs.vols.cmd_dummy import Dummy
from mcdp_docs.vols.cmd_go import GoCommand, DepCommand
from mcdp_docs.vols.cmd_par import ParCommand
from mcdp_docs.vols.cmd_render import RenderCommand
from mcdp_docs.vols.cmd_set import SetCommand
from mcdp_docs.vols.cmd_source import SourceCommand
from mcdp_docs.vols.recipe import Recipe
from mcdp_docs.vols.structures import BuildStatus, ScriptException
from mcdp_utils_misc import locate_files
from mcdp_utils_misc import yaml_load
from quickapp import QuickApp


class Vols(QuickApp):
    """ Render a single document """

    def define_options(self, params):
        params.add_string('out', help='Output dir', default=None)

        params.add_string('-d', help='Destination', default=None)

        params.add_string(name='recipes',
                          short='-r', help='Recipes (comma separated)', default='*')
        params.accept_extra()

    def define_jobs_context(self, context):
        logger.setLevel(logging.DEBUG)

        d = '.'
        recipes = load_recipes(d)
        for name, r in recipes.items():
            print indent(r.summary(), "", name + ': ')

#        context = context.cc

        options = self.get_options()
        spec = options.recipes.split(',')
        use = expand_string(spec, recipes)
        print('using: %s' % use)

        builder = Builder(recipes)
        for name in use:
            bs = builder.build(context, name)
            context.comp(describe_result, name, bs)


class Builder():

    def __init__(self, recipes):
        self.recipes = recipes
        self.name2result = OrderedDict()

    def build(self, context, name, bs0=None):
        if name in self.name2result:
            return self.name2result[name]
        print('building job %s' % name)

        if not name in self.recipes:
            msg = 'Could not find recipe %r' % name
            raise ScriptException(msg)
        recipe = self.recipes[name]

        deps = recipe.get_dependencies()
        deps2result = {}
        for d in deps:
            deps2result[d] = self.build(context, d)

        c = context.child(str(name))
        bs = bs0
        for i, command in enumerate(recipe.commands):
            bs = recipe_jobs(c, 'cmd%s' % (i), command, self.recipes, deps2result, bs)

        self.name2result[name] = bs
        return bs


def describe_result(name, bs):
    print('Results of %s:' % name)
    print bs


def recipe_jobs(context, name, command, recipes, deps2result, bs0=None):
    if bs0 is None:
        bs0 = BuildStatus()

    if isinstance(command, ParCommand):
        partial = []
        for i, c in enumerate(command.commands):
            partial_i = context.comp(recipe_job, c, bs0, deps2result, job_id=str(name) + '-%d' % i)
            partial.append(partial_i)
        return context.comp(merge_bs, partial)
    elif isinstance(command, GoCommand):
        builder = Builder(recipes)
        res = builder.build(context, command.get_name(), bs0)
        return res
    else:
        res = context.comp(recipe_job, command, bs0, deps2result, job_id=str(name))
        return res


def merge_bs(bs_list):
    res = BuildStatus()
    for b in bs_list:
        res.merge(b)
    #print('Merged: %s' % res)
    return res


def recipe_job(command, bs, deps2result):
    if isinstance(command, DepCommand):
        #print('merging results of %s' % command.get_name())
        res = deps2result[command.get_name()]
        bs.merge(res)
        return bs
    else:
        d0 = os.getcwd()
        d = os.path.dirname(command.original_file)
        os.chdir(d)
        try:
            command.go(bs)
        finally:
            os.chdir(d0)
        return bs


vols_entry_main = Vols.get_sys_main()


def cmd_from_line(line):
    tokens = line.split()
    if tokens[0] == 'set':
        assert len(tokens) == 3
        return SetCommand(tokens[1], tokens[2])

    if tokens[0] == 'dep':
        assert len(tokens) == 2
        return DepCommand(tokens[1])

    if tokens[0] == 'do':
        assert len(tokens) == 2
        return GoCommand(tokens[1])

    if tokens[0] == 'par':
        cmd = cmd_from_line(" ".join(tokens[1:]))
        return ParCommand([cmd])

    if tokens[0] == 'source':
        assert len(tokens) == 2
        return SourceCommand(tokens[1])

    if tokens[0] == 'echo':
        return Dummy(line)

    if tokens[0] == 'append':
        return Dummy(line)

    if tokens[0] == 'render':
        return RenderCommand()

    if tokens[0] == 'note_errors':
        return Dummy(line)

    if tokens[0] == 'embed_css':
        return Dummy(line)

    if tokens[0] == 'add_edit_links':
        return Dummy(line)

    if tokens[0] == 'remove_status':
        return Dummy(line)

    if tokens[0] == 'extract_assets':
        return Dummy(line)

    if tokens[0] == 'extract_links':
        return Dummy(line)

    if tokens[0] == 'prince':
        return Dummy(line)

    if tokens[0] == 'split':
        return Dummy(line)

    msg = 'Could not interpret line %r' % line
    raise ValueError(msg)


@contract(data=dict)
def recipe_from_yaml(data):

    lines = [f.strip() for f in data.split('\n')]
    lines = [f for f in lines if f and not f.startswith('#')]
    commands = [cmd_from_line(f) for f in lines]

    res = []
    while commands:
        c = commands.pop(0)
        if isinstance(c, ParCommand) and res and isinstance(res[-1], ParCommand):
            res[-1].commands.extend(c.commands)
        else:
            res.append(c)

    deps = [x.get_name() for x in res if isinstance(x, DepCommand)]

    rec = Recipe(deps, res)
    return rec


@contract(returns=dict)
def load_recipes(dirname):
    files = locate_files(dirname, '*.edition.yaml')
    recipes = OrderedDict()

    for fn in files:
        data = yaml_load(open(fn).read())
        for k, v in data.items():
            recipes[k] = recipe_from_yaml(v)
            recipes[k].set_original_file(os.path.realpath(fn))
    return recipes

