from contracts import contract
from contracts.utils import indent
from mcdp_docs.vols.recipe import  RecipeCommandStatic
from mcdp_utils_misc.augmented_result import AugmentedResult


class ParCommand(RecipeCommandStatic):

    def __init__(self, commands):
        self.commands = commands

    def __repr__(self):
        s = 'Do in parallel:'
        for c in self.commands:
            s += '\n' + indent(str(c), '', ' - ')
        return s

    @contract(bs=AugmentedResult)
    def go(self, bs):
        pass

    def set_original_file(self, fn):
        for c in self.commands:
            c.set_original_file(fn)
        self.original_file = fn
