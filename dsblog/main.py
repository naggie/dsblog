#/usr/bin/env python
import environment
import sys
import logging
import colorlog
from shutil import copytree,rmtree
import jinja2
from os.path import join,isdir
from datetime import datetime
from collections import defaultdict

# TODO count articles for user profiles with reducer function 

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
        environment.loadConfig(sys.argv[1])

    config = environment.getConfig()
    environment.makeDirs()

    # after config is loaded (sue me)
    from discourse import Discourse
    import feed
    from user_profile import AnonymousUserProfile

    output_static_dir = join(config['output_dir'],'static')

    if isdir(output_static_dir):
        rmtree(output_static_dir)

    copytree(config['static_dir'],output_static_dir)

    articles = dict()
    comments = defaultdict(list)
    profiles = defaultdict(AnonymousUserProfile)

    discourse = Discourse(
            api_user = config['api_user'],
            api_key = config['api_key'],
            url = config['url'],
            extra_usernames = [k['username'] for k in config['feed_import']],
        )

    discourse.crawl()

    for article in discourse.articles:
        articles[article.url] = article

    for comment in discourse.comments:
        comments[comment.article_url].append(comment)
        comment.process()

    for profile in discourse.user_profiles:
        profile.process()
        profiles[profile.username] = profile

    for kwargs in config['feed_import']:
        for article in feed.crawl(**kwargs):
            articles[article.url] = article


    for article in articles.values():
        profiles[article.username].article_count +=1
        article.process()


    env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(config['template_dir']),
        )

    env.globals["compile_date"] = datetime.now()


    template = env.get_template('blog.html')
    filepath = join(config['output_dir'],'index.html')
    template.stream(
            articles=sorted(articles.values()),
            profiles=profiles,
            #prefetch=[articles[0].url],
            #prerender=articles[0].url,
    ).dump(filepath)

    template = env.get_template('article_page.html')
    for article in articles.values():
        if article.full:
            filepath = join(config['output_dir'],article.url)
            template.stream(
                profiles=profiles,
                article=article,
                comments=sorted(comments[article.original_url]),
            ).dump(filepath)


    template = env.get_template('about.html')
    filepath = join(config['output_dir'],'about.html')
    template.stream(
            profiles=sorted(profiles.values()),
    ).dump(filepath)

if __name__ == "__main__":
    main()
