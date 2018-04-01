from collections import OrderedDict
import logging
import os

from compmake.plugins.console_banners import name
from compmake.structures import Promise
from contracts import contract
from contracts.utils import indent
from mcdp.logs import logger
from mcdp_cli.utils_wildcard import expand_string
from mcdp_docs.vols.cmd_dummy import Dummy
from mcdp_docs.vols.cmd_go import GoCommand, DepCommand
from mcdp_docs.vols.cmd_par import ParCommand
from mcdp_docs.vols.cmd_render import RenderCommand
from mcdp_docs.vols.cmd_set import SetCommand
from mcdp_docs.vols.cmd_source import SourceCommand, ResourceCommand
from mcdp_docs.vols.recipe import Recipe, RecipeCommandStatic, \
    RecipeCommandDynamic
from mcdp_docs.vols.structures import BuildStatus, ScriptException
from mcdp_utils_misc import locate_files
from mcdp_utils_misc import yaml_load
from mcdp_utils_misc.augmented_result import AugmentedResult
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
        use = expand_string(spec, list(recipes))
        print('using: %s' % use)

        builder = Builder(recipes)
        for name in use:
            bs_aug = builder.build(context, name)
            context.comp(describe_result, name, bs_aug)


class Builder(object):

    def __init__(self, recipes):
        self.recipes = recipes
        self.name2result = OrderedDict()

    @contract(returns=Promise, bs_aug0='None|$AugmentedResult|$Promise')
    def build(self, context, name, bs_aug0=None):
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
        bs_aug = bs_aug0
        for i, command in enumerate(recipe.commands):
            name_ = '%s-cmd%s' % (name, i)
            bs_aug = recipe_jobs(c, name_,
                                 command, self.recipes, deps2result, bs_aug)

        self.name2result[name] = bs_aug
        return bs_aug


def describe_result(name, bs):
    print('Results of %s:' % name)
    print bs


@contract(returns=Promise)
def recipe_jobs(context, name, command, recipes, deps2result, bs_aug0=None):
    if bs_aug0 is None:
        bs_aug0 = AugmentedResult()
        bs_aug0.desc = 'First iteration of recipe_jobs(%s)' % name
        bs_aug0.set_result(BuildStatus())

    if isinstance(command, ParCommand):
        partial = []
        for i, c in enumerate(command.commands):
            partial_i = context.comp_dynamic(recipe_job, c, bs_aug0, deps2result,
                                             job_id=str(name) + '-%d' % i)
            partial.append(partial_i)
        return context.comp(merge_bs, partial)
    elif isinstance(command, GoCommand):
        builder = Builder(recipes)
        res = builder.build(context, command.get_name(), bs_aug0)
        return res
    else:
        res = context.comp_dynamic(recipe_job, command, bs_aug0, deps2result,
                                   job_id=str(name))
        return res


@contract(bs_list='list($AugmentedResult)', returns=AugmentedResult)
def merge_bs(bs_list):
    res_aug = AugmentedResult()
    res = BuildStatus()
    for b_aug in bs_list:
        res.merge(b_aug.get_result())
        res_aug.merge(b_aug)
    #print('Merged: %s' % res)
    res_aug.set_result(res)
    return res_aug


@contract(bs_aug=AugmentedResult, returns='$AugmentedResult|$Promise')
def recipe_job(context, command, bs_aug, deps2result):
    bs = bs_aug.get_result()

    if isinstance(command, DepCommand):
        #print('merging results of %s' % command.get_name())
        res_aug = deps2result[command.get_name()]
        res = res_aug.get_result()
        bs.merge(res)
        bs_aug.merge(res_aug, prefix=command.get_name())
        return bs_aug
    else:
        d0 = os.getcwd()
        d = os.path.dirname(command.original_file)
        os.chdir(d)
        try:
            if isinstance(command, RecipeCommandStatic):
                job_id = type(command).__name__
                return context.comp(simple_apply, command, bs_aug, job_id=job_id)
            elif isinstance(command, RecipeCommandDynamic):
                return command.go_dynamic(context, bs_aug)
            else:
                assert False, command
        finally:
            os.chdir(d0)
        assert False


def simple_apply(command, bs_aug):
    command.go(bs_aug)
    print('After applying: %s' % bs_aug)
    return bs_aug


vols_entry_main = Vols.get_sys_main()


@contract(line=unicode)
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

    if tokens[0] == 'resources':
        assert len(tokens) == 2
        return ResourceCommand(tokens[1])

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


@contract(data=unicode)
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
            # todo: check v unicode
            recipes[k] = recipe_from_yaml(v)
            recipes[k].set_original_file(os.path.realpath(fn))
    return recipes

