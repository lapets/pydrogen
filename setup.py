from distutils.core import setup

setup(
    name             = 'pydrogen',
    version          = '0.0.2.0',
    packages         = ['pydrogen',],
    install_requires = ['ast', 'inspect',],
    license          = 'MIT License',
	url              = 'http://pydrogen.org',
	author           = 'A. Lapets',
	author_email     = 'a@lapets.io',
    description      = 'Python library for building embedded languages within Python that have alternative operational semantics and abstract interpretations.',
    long_description = open('README').read(),
)
