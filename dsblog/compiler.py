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
