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
import yaml

from crawlers.discourse import Discourse
from crawlers.feed import Feed
from localiser import Localizer,Slugger
import sys


if len(sys.argv) != 3:
    print "DSblog aggregator"
    print "Usage: %s <config.yml> <build_dir/>" % sys.argv[0]
    sys.exit()
else:
    build_dir = sys.argv[2]
    with open(sys.argv[1]) as f:
        config = yaml.load(f.read())


#build_dir = 'build/'


build_static_dir = os.path.join(build_dir,'static')
script_dir = os.path.dirname(os.path.realpath(__file__))

if os.path.exists(build_static_dir):
    rmtree(build_static_dir)

copytree('static',build_static_dir)


env = Environment(loader=FileSystemLoader('templates'))


articles = list()
user_profiles = list()

for task in config:
    crawler_name = task["crawler"]
    del task["crawler"]
    if crawler_name == "Discourse":
        crawler = Discourse(**task)
    elif crawler_name == "Feed":
        crawler = Feed(**task)
    else:
        raise NotImplementedError("%s crawler not implemented" % task.crawler)


    print crawler_name + ': %s...' % crawler.url
    crawler.crawl()
    articles += crawler.articles

    # TODO merge down properly
    user_profiles += crawler.user_profiles


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
slugify = Slugger(['index']).slugify
localiser = Localizer(
        local_dir = os.path.join(build_dir,'images'),
        url = 'images/',
)


for profile in user_profiles:
    # TODO remove replacement once SSL certs are fixed
    if profile.get("avatar"):
        profile["avatar"] = profile["avatar"].replace('http://boards.darksky.io','http://localhost:8099')

    profile['avatar'] = localiser.localise(profile['avatar'])


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


template = env.get_template('blog.html')
filepath = os.path.join(build_dir,'index.html')
template.stream(
        articles=articles,
        prefetch=[articles[0]["url"]],
        prerender=articles[0]["url"],
).dump(filepath)

template = env.get_template('article_page.html')
for article in articles:
    if article['local']:
        filepath = os.path.join(build_dir,article['url'])
        template.stream(article=article).dump(filepath)


template = env.get_template('about.html')
filepath = os.path.join(build_dir,'about.html')
template.stream(
        profiles=user_profiles,
).dump(filepath)
