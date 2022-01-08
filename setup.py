from setuptools import setup

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="restuml2code",
    install_requires=[
        'docutils>=0.16,<0.18',
        'mako>=1.1.6'
    ],
    extras_require={
    },
)