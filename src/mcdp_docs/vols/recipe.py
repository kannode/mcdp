

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

    def go(self, bs):
        pass

    def set_original_file(self, fn):
        self.original_file = fn

