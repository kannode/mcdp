
from contracts import contract
from mcdp_docs.vols.recipe import RecipeCommandStatic
from mcdp_utils_misc.augmented_result import AugmentedResult


class Dummy(RecipeCommandStatic):

    def __init__(self, line):
        self.line = line

    @contract(bs_aug=AugmentedResult)
    def go(self, bs_aug):  #@UnusedVariable
        print('Dummy %s' % self.line)

    def __str__(self):
        return '(dummy) %s' % self.line

