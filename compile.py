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

# example article
articles = [
    {
        "title":"3 ways to improve your coffee",
        "url":"google.com",
        "image":"https://placeimg.com/710/100/tech",
        "content":"""Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis 
            aut e irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.""",
        "author_image":"https://placeimg.com/100/100/tech",
        "author_name":"Callan Bryant",
        "published":"2nd January 2015",
    }
 ] *50


template.stream(articles=articles).dump(filepath)
