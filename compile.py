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



class Slugger():
    'Slugify with a memory: emit unique slugs'
    articles.sort(key=lambda a:a['published'],reverse=True)
    slugs = set()

    def __init__(self,initial):
        self.slugs = set(initial)


    def slugify(self,resource):
        initial_slug = re.sub(r'([^\w\.]+|\.\.\. )','-',resource).strip('-').lower()

        count = 0
        slug = initial_slug
        while True:
            if slug not in self.slugs:
                self.slugs.add(slug)
                return slug

            count+=1
            # a file name? add a number before the first dot to be safe
            if '.' in slug:
                parts = initial_slug.split('.')
                parts[-2] += '-%' % count
                slug = '.'.join(parts)
            else:
                slug = initial_slug + '-' + str(count)




# mutate articles suitable for rendering
# * Localise images in HTML
# * Generate post header image
# * Make slug for url path, giving precedence to older articles
# * TODO when user profiles are implemented, add user info
def filter_articles(articles):
    slugify = Slugger(['index']).slugify
    # sort, oldest first (which has slug precedence)
    articles.sort(key=lambda a:a['published'],reverse=False)
    for article in articles:
        article['url'] = slugify(article['title'])+'.html'
        article['local'] = True

    # now, sort for display
    articles.sort(key=lambda a:a['published'],reverse=True)

filter_articles(articles)

template = env.get_template('blog.html')
filepath = os.path.join(build_dir,'index.html')
template.stream(articles=articles).dump(filepath)

template = env.get_template('article_page.html')
for article in articles:
    if article['local']:
        filepath = os.path.join(build_dir,article['url'])
        template.stream(article=article).dump(filepath)
