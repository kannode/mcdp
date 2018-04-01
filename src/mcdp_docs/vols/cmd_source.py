from contracts import contract
from mcdp_docs.mcdp_render_manual import look_for_files
from mcdp_docs.vols.recipe import RecipeCommandStatic
from mcdp_utils_misc.augmented_result import AugmentedResult
from mcdp_utils_misc.path_utils import expand_all


class SourceCommand(RecipeCommandStatic):

    def __init__(self, dirname):
        self.dirname = dirname

    @contract(bs_aug=AugmentedResult)
    def go(self, bs_aug):
        bs = bs_aug.get_result()
        dirname = expand_all(bs.substitute(self.dirname))

        src_dirs = [dirname]
        files = look_for_files(src_dirs, '*.md')
        print('Found %d files.' % len(files))
#        bs.variables['files'].extend(map(str, files))
        bs.files.extend(map(str, files))
        bs.resources_dirs.append(dirname)

    def __str__(self):
        return 'Source %s' % self.dirname


class ResourceCommand(RecipeCommandStatic):

    def __init__(self, dirname):
        self.dirname = dirname

    @contract(bs_aug=AugmentedResult)
    def go(self, bs_aug):
        bs = bs_aug.get_result()
        dirname = expand_all(bs.substitute(self.dirname))

        bs.resources_dirs.append(dirname)

    def __str__(self):
        return 'Resource dir %s' % self.dirname

