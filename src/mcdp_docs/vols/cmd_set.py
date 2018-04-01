import os

from contracts import contract
from mcdp_docs.vols.recipe import  RecipeCommandStatic
from mcdp_utils_misc.augmented_result import AugmentedResult


class SetCommand(RecipeCommandStatic):

    def __init__(self, varname, value):
        self.varname = varname
        self.value = value

    @contract(bs_aug=AugmentedResult)
    def go(self, bs_aug):
        pwd = os.path.dirname(self.original_file)
        others = {'pwd': pwd}
        bs = bs_aug.get_result()
        bs.variables[self.varname] = bs.substitute(self.value, others=others)
        return bs_aug

    def __str__(self):
        return 'Set %r to %r' % (self.varname, self.value)

