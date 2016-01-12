from __future__ import division
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


env = Environment(loader=FileSystemLoader('templates'))


from crawlers.discourse import Discourse
print 'Discourse...'
# TODO decide on an interface
articles = list()

discourse = Discourse(
    url="http://localhost:8099",
    api_user="naggie",
    api_key=os.environ['API_KEY'],
)
discourse.crawl('facility automation')
articles += discourse.articles


class Slugger():
    'Slugify with a memory: emit unique slugs'
    slugs = set()

    def __init__(self,initial=[]):
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
            parts[0] += '-%s' % count
            slug = ''.join(parts)


class Localizer():
    'Localise given remote URLs'
    # original URLS -> filesystem path
    remote_map = dict()

    # new URLS -> filesystem path
    local_map = dict()

    def __init__(self,local_dir,url):

        if not os.path.exists(local_dir):
            os.mkdir(local_dir)

        self.local_dir = local_dir
        self.url = url.strip('/')

        self.slugify = Slugger().slugify


    def localise(self,url):
        'return a new local URL for the given resource, deferring download'
        # data-url? already local
        if url.startswith('data'):
            return url

        if url in self.remote_map:
            return self.url+'/'+os.path.basename(self.remote_map[url])

        filename = self.slugify(url)
        filepath = os.path.join(self.local_dir,filename)

        new_url = self.url + '/' + filename

        self.remote_map[url] = filepath
        self.local_map[new_url] = filepath

        return new_url


    def localise_images(self,html):
        content = BeautifulSoup(html,'html.parser')
        for img in content.find_all('img'):
            img['src'] = self.localise(img["src"])

        return unicode(content)


    def download(self):
        "download all deferred resources if they don't already exist"

        for url,filepath in self.remote_map.items():
            if os.path.exists(filepath):
                del self.remote_map[url]

        if not self.remote_map:
            return

        print "Localising new images..."
        for url,filepath in tqdm(self.remote_map.items(),leave=True):
            try:
                r = requests.get(url, stream=True)
                if r.status_code == 200:
                    with open(filepath, 'wb') as f:
                        for chunk in r:
                            f.write(chunk)
                else:
                    for u,f in self.local_map.items():
                        if f == filepath:
                            del self.local_map[u]
            except requests.exceptions.ConnectionError:
                continue


    def annotate_images(self,html,max_width=710):
        'Add (scaled) width/height to images to prevent DOM reflow thrashing as images are loaded. RUN AFTER DOWNLOAD'
        soup = BeautifulSoup(html, 'html.parser')

        for img in soup.find_all('img'):
            if not img.get("width") or not img.get("height"):
                if img["src"].startswith('data'):
                    # data URI, deterministic as already loaded. No need.
                    return

                filepath = self.local_map[img["src"]]

                try:
                    image = Image.open(filepath)
                except IOError:
                    continue

                factor = min(max_width,image.width)/image.width
                img['width'] = int(image.width*factor)
                img['height'] = int(image.height*factor)

        return unicode(soup)


def make_header_image(img):
    img = img.resize((710,int(img.height*710/img.width)),Image.ANTIALIAS)
    img = img.crop((
        0,
        int(img.height/2)-50,
        710,
        int(img.height/2)+50,
    ))
    return img





# mutate articles suitable for rendering
# * Localise images in HTML
# * Generate post header image
# * Make slug for url path, giving precedence to older articles
# * TODO when user profiles are implemented, add user info
def filter_articles(articles):
    slugify = Slugger(['index']).slugify
    localiser = Localizer(
            local_dir = os.path.join(build_dir,'images'),
            url = 'images/',
    )

    # sort, oldest first (which has slug precedence)
    articles.sort(key=lambda a:a['published'],reverse=False)
    for article in articles:
        article['url'] = slugify(article['title'])+'.html'
        article['local'] = True

        # TODO remove replacement once SSL certs are fixed
        article["content"] = article["content"].replace('http://boards.darksky.io','http://localhost:8099')
        if article.get("image"):
            article["image"] = article["image"].replace('http://boards.darksky.io','http://localhost:8099')
        if article.get("author_image"):
            article["author_image"] = article["author_image"].replace('http://boards.darksky.io','http://localhost:8099')

        article['content'] = localiser.localise_images(article['content'])
        article['author_image'] = localiser.localise(article['author_image'])

        if article.get('image'):
            filename = slugify('header-'+article['image'])
            filepath = os.path.join(build_dir,'images',filename)

            src = article['image']
            article['image'] = 'images/'+filename

            if not os.path.exists(filepath):
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

        excerpt = unicode()
        content = BeautifulSoup(article['content'],'html.parser')
        for p in content.find_all('p'):
            for img in p.find_all('img'):
                img.extract()

            excerpt += unicode(p)
            if len(excerpt) > 140:
                break


        article['excerpt'] = excerpt

        for c in article['comments']:
            # TODO remove replacement once SSL certs are fixed
            c["content"] = c["content"].replace('http://boards.darksky.io','http://localhost:8099')
            if c.get("author_image"):
                c["author_image"] = c["author_image"].replace('http://boards.darksky.io','http://localhost:8099')

            c['content'] = localiser.localise_images(c["content"])
            c['author_image'] = localiser.localise(c['author_image'])


    localiser.download()

    print "Annotating images..."
    for article in tqdm(articles,leave=True):
        article["content"] = localiser.annotate_images(article["content"])


        if article.get("comments"):
            for comment in article["comments"]:
                comment["content"] = localiser.annotate_images(comment["content"])




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
