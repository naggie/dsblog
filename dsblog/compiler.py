#/usr/bin/env python
from __future__ import division
from jinja2 import Environment, FileSystemLoader
from urlparse import urlparse
from iso8601 import parse_date
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
import json

from datetime import datetime

def main():
    if len(sys.argv) != 3:
        print "DSblog aggregator"
        print "Usage: %s <config.yml> <build_dir/>" % sys.argv[0]
        sys.exit()
    else:
        build_dir = sys.argv[2]
        with open(sys.argv[1]) as f:
            config = yaml.load(f.read())



    if os.path.exists(build_static_dir):
        rmtree(build_static_dir)

    copytree(os.path.join(script_dir,'static'),build_static_dir)


    env = Environment(loader=FileSystemLoader(os.path.join(script_dir,'templates')))
    env.filters["domain"] = lambda url: urlparse(url).netloc
    env.globals["compile_date"] = datetime.now()


    articles = list()
    user_profiles = list()


    # merge with previous archive (some posts may have changed or may have
    # vanished entirely)
    # Articles may vanish if the RSS (or whatever) feed only displays the last
    # 15 or so items. Users, which are valuable for attribution, may be banned
    # or have their account deleted. The posts should not vanish implicitly
    # because of this, it should be a manual process.
    articles_json_filepath = os.path.join(build_dir,'articles.json')
    user_profiles_json_filepath = os.path.join(build_dir,'user_profiles.json')
    # load previous articles
    if os.path.exists(articles_json_filepath):
        with open(articles_json_filepath) as f:
            for old in json.loads(f.read()):
                old["published"] = parse_date(old["published"])
                for new in articles:
                    if old["url"] == new["url"]:
                        break
                else:
                    articles.append(old)

    # load previous missing user_profiles
    if os.path.exists(user_profiles_json_filepath):
        with open(user_profiles_json_filepath) as f:
            for old in json.loads(f.read()):
                for new in user_profiles:
                    if old["username"] == new["username"]:
                        break
                else:
                    user_profiles.append(old)

    # archive again
    # TODO should probably be pre-filter
    with open(articles_json_filepath,'w') as f:
        f.write(json.dumps(
            articles,
            sort_keys=True,
            indent=4,
            separators=(',', ': '),
            default=lambda d: d.isoformat(),
        ))

    with open(user_profiles_json_filepath,'w') as f:
        f.write(json.dumps(
            user_profiles,
            sort_keys=True,
            indent=4,
            separators=(',', ': '),
            default=lambda d: d.isoformat(),
        ))



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

        # get user
        for profile in user_profiles:
            if article["username"] == profile["username"]:
                article['author_name'] = profile["name"]
                article['author_image'] = profile["avatar"]
                article['author_url'] = profile["website"]
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
                    c['author_url'] = profile["website"]
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
