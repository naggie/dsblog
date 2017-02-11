import yaml
from iso8601 import parse_date
from user_profile import AnonymousUserProfile
from collections import defaultdict
from environment import getConfig
import logging

# PYYAML bug -- cannot roundtrip datetime with TZ http://pyyaml.org/ticket/202
# https://stackoverflow.com/questions/13294186/can-pyyaml-parse-iso8601-dates
yaml.add_constructor(u'tag:yaml.org,2002:timestamp', lambda loader,node: parse_date(node.value))

log = logging.getLogger(__name__)
config = getConfig()


class Database(object):
    def __init__(self):
        try:
            with open(config['database_file']) as f:
                data = yaml.load(f)
                self.articles = data['articles']
                self.comments = data['comments']
                self.profiles = data['profiles']
        except IOError:
            # articles by URL
            self.articles = dict()

            # comments by article URL by comment pubdate.isoformat()
            self.comments = defaultdict(dict)

            # user profiles by username.
            self.profiles = defaultdict(AnonymousUserProfile)

    def assert_articles(self,articles):
        # "Thrashing"
        # some articles may have nominally mutated but have the same revision,
        # for example when discourse replaces images. Semantically the content
        # has not changed if the revision number hasn't changed. Don't replace
        # the article or process the article in this case, it it would mean
        # downloading duplicate images for no reason and make roundtrips
        # non-idempotent.

        for article in articles:
            try:
                existing = self.articles[article.original_url]
                if article.revision != existing.revision and not getattr(article,'degraded',False):
                    log.info('Article updated:  %s',article.original_url)
                    article.process()
                    self.articles[article.original_url] = article
            except KeyError:
                log.info('New article: %s',article.original_url)
                article.process()
                self.articles[article.original_url] = article

    def assert_comments(self,comments):
        for comment in comments:
            try:
                existing = self.comments[comment.article_url][comment.pubdate.isoformat()]
                if comment.revision != existing.revision:
                    comment.process()
                    self.comments[comment.article_url][comment.pubdate.isoformat()] = comment
            except KeyError:
                comment.process()
                self.comments[comment.article_url][comment.pubdate.isoformat()] = comment


    def assert_profiles(self,profiles):
        # no "Thrashing" with profiles as there is (normally) one image which
        # is known
        for profile in profiles:
            profile.process()
            self.profiles[profile.username] = profile


    def get_article_list(self):
        return sorted(self.articles.values())

    def get_profile_dict(self):
        self._count_user_articles()
        return self.profiles

    def get_profile_list(self,publishers_only=True):
        self._count_user_articles()

        if publishers_only:
            return sorted([p for p in self.profiles.values() if p.article_count])
        else:
            return sorted(self.profiles.values())


    def get_comment_list(self,article):
        return sorted(self.comments[article.original_url].values())


    def _count_user_articles(self):
        # update article count, as well
        for profile in self.profiles.values():
            profile.article_count = 0

        for article in self.articles.values():
            self.profiles[article.username].article_count +=1


    def save(self):
        with open(config['database_file'],'w') as f:
            yaml.dump({
                'articles':self.articles,
                'comments':self.comments,
                'profiles':self.profiles,
            },f)

