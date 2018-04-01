from abc import abstractmethod, ABCMeta

from contracts import contract
from mcdp_utils_misc.augmented_result import AugmentedResult


class Recipe(object):

    def __init__(self, deps, commands):
        self.commands = commands
        self.deps = deps
        self.original_file = None
        for c in self.commands:
            c.set_original_file(self.original_file)

    def get_dependencies(self):
        return self.deps

    def summary(self):
        s = "Recipe"
#        if self.deps:
        s += ' (deps: %s)' % self.deps
        for c in self.commands:
            s += '\n  - %s' % c

        s += '\n Original file: %s ' % self.original_file
        return s

    def set_original_file(self, fn):
        self.original_file = fn
        for c in self.commands:
            c.set_original_file(fn)


class RecipeCommand(object):
    __metaclass__ = ABCMeta

    def set_original_file(self, fn):
        self.original_file = fn


class RecipeCommandStatic(RecipeCommand):

    @abstractmethod
    @contract(bs_aug=AugmentedResult)
    def go(self, bs_aug):
        pass


class RecipeCommandDynamic(RecipeCommand):

    @abstractmethod
    @contract(bs_aug=AugmentedResult)
    def go_dynamic(self, context, bs_aug):
        pass

