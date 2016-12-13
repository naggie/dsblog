#/usr/bin/env python
from config import getConfig, loadConfig
import sys
import logging
import colorlog
from shutil import copytree,rmtree

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter('%(asctime)s  %(log_color)s%(levelname)s%(reset)s %(name)s: %(message)s'))
logger = colorlog.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# reduce spam
logging.getLogger("requests").setLevel(logging.WARNING)

def init(config):
    copytree(os.path.join(script_dir,'static'),config['build_dir'])

def main():
    if len(sys.argv) != 2:
        print "DSblog aggregator"
        print "Usage: %s <config.yml>" % sys.argv[0]
        sys.exit()
    else:
        loadConfig(sys.argv[1])

    config = getConfig()

    # after config is loaded (sue me)
    from discourse import Discourse
    import feed


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
