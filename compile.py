from jinja2 import Environment, FileSystemLoader
import os
import re
from shutil import copytree,rmtree


build_dir = 'build/'

#if os.path.exists(build_dir):
#    raise IOError('Remove build directory first')


build_static_dir = os.path.join(build_dir,'static')
build_image_dir = os.path.join(build_dir,'images')
script_dir = os.path.dirname(os.path.realpath(__file__))

if os.path.exists(build_static_dir):
    rmtree(build_static_dir)
copytree('static',build_static_dir)


env = Environment(loader=FileSystemLoader('templates'))


from crawlers.discourse import Discourse
print 'Discourse...'
# TODO decide on an interface
articles = Discourse(
    url="http://localhost:8099",
    api_user="naggie",
    api_key=os.environ['API_KEY'],
).list_articles('dj')


def slugify(resource):
    return re.sub(r'[^\w\.]+','-',resource).strip('-').lower()


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
