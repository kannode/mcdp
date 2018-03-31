from mcdp_docs.mcdp_render_manual import look_for_files
from mcdp_docs.vols.recipe import RecipeCommand


class SourceCommand(RecipeCommand):

    def __init__(self, dirname):
        self.dirname = dirname

    def go(self, bs):
        dirname = bs.substitute(self.dirname)
        src_dirs = [dirname]
        files = look_for_files(src_dirs, '*.md')

        bs.files.append(files)

        print bs.filesystem

    def __str__(self):
        return 'Source %s' % self.dirname

