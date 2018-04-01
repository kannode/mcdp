from contracts import contract
from mcdp_docs.vols.recipe import  RecipeCommandStatic
from mcdp_utils_misc.augmented_result import AugmentedResult


class GoCommand(RecipeCommandStatic):

    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name

    @contract(bs_aug=AugmentedResult)
    def go(self, bs_aug):
        pass

    def __str__(self):
        return 'Execute recipe %r' % self.name


class DepCommand(RecipeCommandStatic):

    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name

    @contract(bs_aug=AugmentedResult)
    def go(self, bs_aug):
        pass

    def __str__(self):
        return 'Dep recipe %r' % self.name

