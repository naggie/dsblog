from jinja2 import Environment, FileSystemLoader
import os
import re
from shutil import copytree,rmtree
from PIL import Image
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
from StringIO import StringIO


build_dir = 'build/'

#if os.path.exists(build_dir):
#    raise IOError('Remove build directory first')


build_static_dir = os.path.join(build_dir,'static')
script_dir = os.path.dirname(os.path.realpath(__file__))

if os.path.exists(build_static_dir):
    rmtree(build_static_dir)

copytree('static',build_static_dir)

if not os.path.exists(os.path.join(build_dir,'images')):
    os.mkdir(os.path.join(build_dir,'images'))

env = Environment(loader=FileSystemLoader('templates'))


from crawlers.discourse import Discourse
print 'Discourse...'
# TODO decide on an interface
articles = Discourse(
    url="http://localhost:8099",
    api_user="naggie",
    api_key=os.environ['API_KEY'],
).list_articles('facility automation')



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
            parts = list(os.path.splitext(initial_slug))
            parts[0] += '-%s' % initial_slug
            slug = ''.join(parts)


def make_header_image(img):
    return img


# mutate articles suitable for rendering
# * Localise images in HTML
# * Generate post header image
# * Make slug for url path, giving precedence to older articles
# * TODO when user profiles are implemented, add user info
def filter_articles(articles):
    slugify = Slugger(['index']).slugify
    # sort, oldest first (which has slug precedence)
    articles.sort(key=lambda a:a['published'],reverse=False)
    for article in tqdm(articles):
        article['url'] = slugify(article['title'])+'.html'
        article['local'] = True

        content = BeautifulSoup(article['content'],'html.parser')
        for img in content.find_all('img'):
            filename = slugify(img['src'])
            filepath = os.path.join(build_dir,'images',filename)

            # TODO remove replacement once SSL certs are fixed
            src = img['src'].replace('http://boards.darksky.io','http://localhost:8099')

            img['src'] = 'images/'+filename

            if os.path.exists(filepath):
                continue

            r = requests.get(src, stream=True)
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r:
                    f.write(chunk)

        article['content'] = unicode(content)

        if article.get('image'):
            filename = slugify('header-'+article['image'])
            filepath = os.path.join(build_dir,'images',filename)

            if os.path.exists(filepath):
                continue

            # TODO perhaps create manifest of images to download

            src = article['image'].replace('http://boards.darksky.io','http://localhost:8099')
            article['image'] = 'images/'+filename
            response = requests.get(src)
            response.raise_for_status()
            imgdata = StringIO(response.content)
            try:
                img = Image.open(imgdata)
                img = make_header_image(img)
                img.save(filepath)
            except IOError:
                article['image'] = None
                pass





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
