from jinja2 import Environment, FileSystemLoader
import os
from shutil import copytree

build_dir = 'build/'
#
script_dir = os.path.dirname(os.path.realpath(__file__))


copytree('static', os.path.join(build_dir,'static') )


env = Environment(loader=FileSystemLoader('templates'))

template = env.get_template('blog.html')
filepath = os.path.join(build_dir,'index.html')
template.stream().dump(filepath)
