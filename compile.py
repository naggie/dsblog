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


# TODO proper interface
from crawlers.discourse import Discourse
import os
# TODO decide on an interface

print 'Discourse...'
articles = Discourse(
    url="http://localhost:8099",
    api_user="naggie",
    api_key=os.environ['API_KEY'],
).list_articles('dj')


# mutate articles suitable for rendering
# * Localise images in HTML
# * Generate post header image
# * Make slug for url path, giving precedence to older articles
# * TODO when user profiles are implemented, add user info
def filter_articles(articles):
    articles.sort(key=lambda a:a['published'],reverse=True)


filter_articles(articles)
template = env.get_template('blog.html')
filepath = os.path.join(build_dir,'index.html')
template.stream(articles=articles).dump(filepath)
