from setuptools import find_packages, setup


def get_version(filename):
    import ast
    version = None
    with open(filename) as f:
        for line in f:
            if line.startswith('__version__'):
                version = ast.parse(line).body[0].value.s
                break
        else:
            raise ValueError('No version found in %r.' % filename)
    if version is None:
        raise ValueError(filename)
    return version


mcdp_version = get_version(filename='src/mcdp/branch_info.py')

setup(name='PyMCDP',
      url='http://github.com/AndreaCensi/mcdp',
      maintainer="Andrea Censi",
      maintainer_email="acensi@idsc.mavt.ethz.ch",
      description='PyMCDP is an interpreter and solver for Monotone Co-Design Problems',
      long_description='',
      keywords="Optimization",
      classifiers=[
          'Development Status :: 4 - Beta',
      ],

      version=mcdp_version,
      download_url='http://github.com/AndreaCensi/mcdp/tarball/%s' % mcdp_version,
      package_dir={'': 'src'},
      packages=find_packages('src'),
      install_requires=[
          'pint',
          'watchdog',
          'decorator',
          'networkx>=1.11,<2',
          'pygments',
          'pyramid',
          'pyramid_jinja2',
          'pyramid_debugtoolbar',
          'nose',
          'beautifulsoup4>=4.6',
          'PyContracts>=1.8.3,<2',
          'ConfTools>=1.7,<2',
          'comptests>=1.4.23,<2',
          'RepRep>=2.9.3,<3',
          'DecentLogs>=1.1.2,<2',
          'QuickApp>=1.3.10,<2',
          'compmake>=3.5.28,<4',
          'networkx>=1.11,<2',
          'psutil',
          'setproctitle',
          'markdown',
          'bcrypt',
          'waitress',
          'lxml',
          'junit_xml',
          'gitpython',
          'authomatic',
          'ruamel.yaml',
          'python-dateutil',
          'chardet',
          'pillow',
          'ruamel.yaml',
          'pygments_markdown_lexer',
          'circleclient',
      ],

      tests_require=[
          'webtest',
          'nose>=1.1.2,<2',
          'selenium>=3.3.1,<4f',
      ],

      # This avoids creating the egg file, which is a zip file, which makes our data
      # inaccessible by dir_from_package_name()
      zip_safe=False,

      # without this, the stuff is included but not installed
      include_package_data=True,

      entry_points={
          'paste.app_factory': ['app=mcdp_web:app_factory'],

          'console_scripts': [
              'mcdp-plot = mcdp_cli:mcdp_plot_main',
              'mcdp-solve = mcdp_cli:mcdp_solve_main',
              'mcdp-web = mcdp_web:mcdp_web_main',
              'mcdp-eval = mcdp_cli:mcdp_eval_main',
              'mcdp-render = mcdp_docs:mcdp_render_main',
              'mcdp-render-manual = mcdp_docs:mcdp_render_manual_main',
              'mcdp-depgraph = mcdp_depgraph:mcdp_depgraph_main',
              'mcdp-load-all = mcdp_hdb_mcdp:mcdp_load_all_main',
              'mcdp-split = mcdp_docs.split:split_main',
              'mcdp-docs-compose = mcdp_docs.composing:compose_main',
              'mcdp-prerender = mcdp_docs.prerender_math:prerender_main',
          ]
      }
      )
