#/usr/bin/env python
import yaml
import sys
from discourse import Discourse
import feed
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter('%(asctime)s  %(log_color)s%(levelname)s%(reset)s %(name)s: %(message)s'))
logger = colorlog.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# reduce spam
logging.getLogger("requests").setLevel(logging.WARNING)

def main():
    if len(sys.argv) != 2:
        print "DSblog aggregator"
        print "Usage: %s <config.yml>" % sys.argv[0]
        sys.exit()
    else:
        with open(sys.argv[1]) as f:
            config = yaml.load(f.read())


    articles = dict()
    comments = dict()
    user_profiles = dict()

    discourse = Discourse(
            api_user = config['api_user'],
            api_key = config['api_key'],
            url = config['url'],
        )

    discourse.crawl()

    for article in discourse.articles:
        articles[article.url] = article

    for kwargs in config['feed_import']:
        for article in feed.crawl(**kwargs):
            articles[article.url] = article



if __name__ == "__main__":
    main()
