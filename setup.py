#!/usr/bin/env python
try:
    from setuptools import setup
    extra = dict(include_package_data=True)
except ImportError:
    from distutils.core import setup
    extra = {}

def do_setup():
    files = ['pysprinklers/*']
    install_requires = ['boto==2.10.0', 'argparse>=1.2.1', 'flask']

    setup(
        name        = 'pysprinklers',
        version     = '1',
        description = 'System for managing sprinklers',
        author      = 'Eli Ribble',
        author_email    = 'junk+pysprinklers@theribbles.org',
        install_requires    = install_requires,
        packages            = ['pysprinklers'],
        package_data        = {'pysprinklers': files},
        scripts             = ['bin/sprinklerd', 'bin/sprinklerctl'],
        data_files          = [('webserver', ['webserver/index.html'])],
        **extra
    )

if __name__ == '__main__':
    do_setup()
