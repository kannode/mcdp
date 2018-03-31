from mcdp_docs.vols.recipe import RecipeCommand


class SetCommand(RecipeCommand):

    def __init__(self, varname, value):
        self.varname = varname
        self.value = value

    def go(self, bs):
        bs.variables[self.varname] = bs.substitute(self.value)

    def __str__(self):
        return 'Set %r to %r' % (self.varname, self.value)

