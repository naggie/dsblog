from jinja2 import Environment, FileSystemLoader
import os
from shutil import copytree,rmtree

build_dir = 'build/'

#if os.path.exists(build_dir):
#    raise IOError('Remove build directory first')


build_static_dir = os.path.join(build_dir,'static')
script_dir = os.path.dirname(os.path.realpath(__file__))

if os.path.exists(build_static_dir):
    rmtree(build_static_dir)
copytree('static',build_static_dir)


env = Environment(loader=FileSystemLoader('templates'))

template = env.get_template('blog.html')
filepath = os.path.join(build_dir,'index.html')
template.stream().dump(filepath)
