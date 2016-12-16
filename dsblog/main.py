#/usr/bin/env python
import environment
import sys
import logging
import colorlog
from shutil import copytree,rmtree
import jinja2
from os.path import join,isdir
from datetime import datetime

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
        environment.loadConfig(sys.argv[1])

    config = environment.getConfig()
    environment.makeDirs()

    # after config is loaded (sue me)
    from discourse import Discourse
    import feed
    from database import Database

    output_static_dir = join(config['output_dir'],'static')

    if isdir(output_static_dir):
        rmtree(output_static_dir)

    copytree(config['static_dir'],output_static_dir)

    database = Database()

    discourse = Discourse(
            api_user = config['discourse_api_user'],
            api_key = config['discourse_api_key'],
            url = config['discourse_url'],
            category = config['discourse_category'],
            extra_usernames = [k['username'] for k in config['feed_import']],
        )

    discourse.crawl()
    database.assert_articles(discourse.articles)
    database.assert_profiles(discourse.user_profiles)
    database.assert_comments(discourse.comments)


    for kwargs in config['feed_import']:
        database.assert_articles( feed.crawl(**kwargs) )

    database.save()


    env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(config['template_dir']),
        )

    # TODO footer/header/description/logo from comment here
    env.globals["compile_date"] = datetime.now()
    env.globals["site_name"] = config["site_name"]
    env.globals["base_url"] = config["base_url"]
    env.globals["description"] = config["site_description"]
    env.globals["extra_links"] = config["extra_links"]
    env.globals["copyright_msg"] = config["copyright_msg"]
    env.globals["copyright_from"] = config["copyright_from"]
    env.globals["footer_msg"] = config["footer_msg"]


    template = env.get_template('blog.html')
    filepath = join(config['output_dir'],'index.html')
    template.stream(
            articles=database.get_article_list(),
            profiles=database.get_profile_dict(),
            #prefetch=[articles[0].url],
            #prerender=articles[0].url,
    ).dump(filepath)

    template = env.get_template('article_page.html')
    for article in database.get_article_list():
        if article.full:
            filepath = join(config['output_dir'],article.url)
            template.stream(
                profiles=database.get_profile_dict(),
                article=article,
                comments=database.get_comment_list(article),
            ).dump(filepath)


    template = env.get_template('about.html')
    filepath = join(config['output_dir'],'about.html')
    template.stream(
            profiles=database.get_profile_list(publishers_only=True),
    ).dump(filepath)

if __name__ == "__main__":
    main()
