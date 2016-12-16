from setuptools import setup, find_packages
import os
from os import path
script_dir = os.path.dirname(os.path.realpath(__file__))

packages = list()
links = list()
with open(path.join(script_dir,'requirements.txt')) as f:
    for line in f:
        if line.startswith('#'):
            continue
        if '#egg' in line:
            links.append(line)
            packagespec = line.split('#egg=')[1].replace('-','==')
            packages.append(packagespec)
        else:
            packages.append(line)

setup(
    name = "dsblog",
    version = "2.2",
    packages = find_packages(),
    dependency_links=links,
    #scripts = ['dsblog/dsblog.py'],
    entry_points = {
        'console_scripts': [
            'dsblog = dsblog.main:main',
            ],
        },
    install_requires = packages,
    package_data = {'':['*.*']},
    author = "Callan Bryant",
    author_email = "callan.bryant@gmail.com",
    maintainer = "Callan Bryant",
    maintainer_email = "callan.bryant@gmail.com",
    description = "Discourse-powered static blog generator",
    license = "MIT",
    keywords = "discourse",
    url = "https://darksky.io/",
)
