
from mcdp_docs.vols.recipe import RecipeCommand


class Dummy(RecipeCommand):

    def __init__(self, line):
        self.line = line

    def go(self, bs):
        print('Dummy %s' % self.line)

    def __str__(self):
        return '(dummy) %s' % self.line

