#/usr/bin/env python
from __future__ import division
from jinja2 import Environment, FileSystemLoader
from urlparse import urlparse
import os
import re
from shutil import copytree,rmtree
from PIL import Image
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
from StringIO import StringIO
import yaml
from collections import Counter
from crawlers.discourse import Discourse
from crawlers.feed import Feed
from localiser import Localizer,Slugger
import sys

def main():
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
    env.filters["domain"] = lambda url: urlparse(url).netloc



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
    slugify = Slugger(['index']).slugify
    localiser = Localizer(
            local_dir = os.path.join(build_dir,'images'),
            url = 'images/',
    )


    for profile in user_profiles:
        profile['avatar'] = localiser.localise(profile['avatar'])


    # sort, oldest first (which has slug precedence)
    articles.sort(key=lambda a:a['published'],reverse=False)
    for article in articles:
        article['origin'] = article["url"]
        if article["content"]:
            article['url'] = slugify(article['title'])+'.html'

        if article.get("content"):
            article['content'] = localiser.localise_images(article['content'])

        if article.get('image'):
            filename = slugify('header-'+article['image'])
            filepath = os.path.join(build_dir,'images',filename)

            src = article['image']
            article['image'] = 'images/'+filename

            if not os.path.exists(filepath):
                response = requests.get(src,verify=False)
                response.raise_for_status()
                imgdata = StringIO(response.content)
                try:
                    img = Image.open(imgdata)
                    img = make_header_image(img)
                    img.save(filepath)
                except IOError:
                    article['image'] = None
                    pass

        # get user
        for profile in user_profiles:
            if article["username"] == profile["username"]:
                article['author_name'] = profile["name"]
                article['author_image'] = profile["avatar"]
                break
        else:
            article["author_name"] = "Anonymous"



        for c in article['comments']:
            c['content'] = localiser.localise_images(c["content"])

            # get user
            for profile in user_profiles:
                if c["username"] == profile["username"]:
                    c['author_name'] = profile["name"]
                    c['author_image'] = profile["avatar"]
                    break
            else:
                c["author_name"] = "Anonymous"


    localiser.download()

    print "Annotating images..."
    for article in tqdm(articles,leave=True):
        if article.get('content'):
            article["content"] = localiser.annotate_images(article["content"])


        if article.get("comments"):
            for comment in article["comments"]:
                comment["content"] = localiser.annotate_images(comment["content"])


    # now, sort for display
    articles.sort(key=lambda a:a['published'],reverse=True)


    # add post count to user profiles then sort
    article_count = Counter()
    for article in articles:
        article_count[article["username"]] +=1

    for profile in user_profiles:
        profile["article_count"] = article_count[profile["username"]]

    user_profiles.sort(key=lambda p:p['article_count'],reverse=True)

    template = env.get_template('blog.html')
    filepath = os.path.join(build_dir,'index.html')
    template.stream(
            articles=articles,
            prefetch=[articles[0]["url"]],
            prerender=articles[0]["url"],
    ).dump(filepath)

    template = env.get_template('article_page.html')
    for article in articles:
        if article['content']:
            filepath = os.path.join(build_dir,article['url'])
            template.stream(article=article).dump(filepath)


    template = env.get_template('about.html')
    filepath = os.path.join(build_dir,'about.html')
    template.stream(
            profiles=user_profiles,
    ).dump(filepath)

if __name__ == "__main__":
    main()
