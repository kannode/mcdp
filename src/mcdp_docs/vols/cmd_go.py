from mcdp_docs.vols.recipe import RecipeCommand


class GoCommand(RecipeCommand):

    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def go(self, bs):
        pass

    def __str__(self):
        return 'Execute recipe %r' % self.name


class DepCommand(RecipeCommand):

    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def go(self, bs):
        pass

    def __str__(self):
        return 'Dep recipe %r' % self.name

