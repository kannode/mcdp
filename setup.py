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

version = get_version(filename='src/mcdp/branch_info.py')

name = 'PyMCDP'

setup(name=name,
      url='http://github.com/AndreaCensi/mcdp',
      maintainer="Andrea Censi",
      maintainer_email="acensi@idsc.mavt.ethz.ch",
      description='PyMCDP is an interpreter and solver for Monotone Co-Design Problems',
      long_description='',
      keywords="Optimization",
      classifiers=[
        'Development Status :: 4 - Beta',
      ],

      version=version,

      download_url=
        'http://github.com/AndreaCensi/mcdp/tarball/%s' % version,

      package_dir={'':'src'},
      packages=find_packages('src'),
      install_requires=[
        #'ConfTools>=1.0,<2',
        # '#quickapp',
        # 'reprep',
        'pint',
        'watchdog',
        'decorator',
        'networkx',
        'pygments',
          'pyramid',
        'pyramid_jinja2',
        #'pyramid_chameleon',
        'pyramid_debugtoolbar',
        'nose',

        'beautifulsoup4>=4.6',
        'PyContracts>=1.8.0,<2',
        'ConfTools>=1.7,<2',
        'comptests>=1.4.23,<2',
        'RepRep>=2.9.3,<3',
        'DecentLogs>=1.1.2,<2',
        'QuickApp>=1.3.10,<2',
        'compmake>=3.5.20,<4',
        'psutil',
        'setproctitle',
        'markdown',
        'bcrypt',
        'waitress',
        'lxml',
        'junit_xml',
        'gitpython',
        'authomatic',
        'webtest',
        'ruamel.yaml',
        'python-dateutil',
        'chardet',
        'pillow',
        'ruamel.yaml',
        'pygments_markdown_lexer',
      ],
      # This avoids creating the egg file, which is a zip file, which makes our data
      # inaccessible by dir_from_package_name()
      zip_safe = False,
        # without this, the stuff is included but not installed
        include_package_data=True,

      dependency_links  = [
          # 'https://github.com/AndreaCensi/contracts/archive/env_mcdp.zip#egg=PyContracts',
          # 'https://github.com/AndreaCensi/conf_tools/archive/env_fault.zip#egg=ConfTools',
          # 'https://github.com/AndreaCensi/quickapp/archive/env_fault.zip#egg=QuickApp',
          # 'git+https://github.com/AndreaCensi/quickapp.git@env_mcdp#egg=QuickApp',
          # 'https://github.com/AndreaCensi/reprep/archive/env_mcdp.zip#egg=RepRep',
          # 'https://github.com/AndreaCensi/gvgen/archive/master.zip#egg=gvgen-0.9.1',
      ],

      tests_require=[
        'nose>=1.1.2,<2',
        'selenium>=3.3.1,<4f',
      ],

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
        ]
      }
)
