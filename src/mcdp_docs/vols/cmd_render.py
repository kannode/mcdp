from mcdp_docs.vols.recipe import RecipeCommand


class RenderCommand(RecipeCommand):

    def __init__(self):
        pass

    def go(self, bs):
        print('Rendering')
        with bs.filesystem.capture():
            with open('out.html', 'w') as f:
                f.write('hello!')

        print bs.filesystem

    def __str__(self):
        return 'Render'

