# may factor into generic crawler interface + processor
import requests
from iso8601 import parse_date
import re
from bs4 import BeautifulSoup
import logging
from article import Article,Comment
from user_profile import UserProfile
from environment import getConfig
from database import yaml
from hashlib import sha256


config = getConfig()

# TODO publish articles (idempotent)

article_notice = u"""**This article has been imported from dsblog running on {site_name}
discussion. Any comments you leave here will appear on the {site_name}.**
```
{header}#canary: {canary}
```
----
{article}
"""

log = logging.getLogger(__name__)


def get_meta(html):
    'parse yaml from first HTML code block'
    content = BeautifulSoup(html,'html.parser')

    raw = content.find_all('code')

    if not raw:
        return {}

    return yaml.load(raw.string)


class Discourse():
    def __init__(self,url,api_user,api_key,category="Blog",extra_usernames=[]):
        self.url = url
        self.api_key = api_key
        self.api_user = api_user
        self.category = category

        self.articles = list()
        self.comments = list()
        self.user_profiles = list()

        self.usernames = set(extra_usernames)

        self.crawled = False

    def get(self,*path,**params):
        'get an API URL where list path is transformed into a JSON request and parsed'
        parts = [self.url] + [str(p) for p in path]

        params.update({
            'api_user':self.api_user,
            'api_key':self.api_key,
        })

        response = requests.get(
                url = '/'.join(parts) + '.json',
                params=params,
        )
        response.raise_for_status()

        return response.json()


    def post(self,*path,**data):
        'Post some data'
        parts = [self.url] + [str(p) for p in path]

        data.update({
            'api_user':self.api_user,
            'api_key':self.api_key,
        })

        response = requests.post(
                url='/'.join(parts),
                data=data,
        )
        response.raise_for_status()

        return response.json()


    def normalise_html(self,html):
        content = BeautifulSoup(html,'html.parser')
        # repair all protocol-less URLS
        for img in content.find_all('img'):
            if img['src'].startswith('//'):
                img['src'] = self.url.split('//')[0] + img['src']

        # repair all domain-less
        for img in content.find_all('img'):
            if img['src'].startswith('/'):
                img['src'] = self.url + img['src']

        for a in content.find_all('a'):
            if a['href'].startswith('//'):
                a['href'] = self.url.split('//')[0] + a['href']

        # remove useless meta links (a discourse-ism)
        for div in content.find_all('div',class_="meta"):
            div.extract()

        return content.prettify(formatter="html")

    def crawl(self):
        # TODO support more_posts for result pagination so articles are not missed
        # find cetegory ID
        for cat in self.get('categories')['category_list']['categories']:
            id = cat['id']
            if self.category.lower() == cat['name'].lower():
                # correct case
                self.category = cat['name']
                break
        else:
            raise IOError('Could not find category: %s'%name)

        # list topic IDs, collect usernames
        ids = list()
        for t in self.get('c',id)['topic_list']['topics']:
            ids.append(t["id"])


        # load topics (containing posts: article then comments)
        for id in ids:
            topic = self.get('t',id)
            first_post = topic['post_stream']['posts'][0]

            self.usernames.add(first_post['username'])

            # don't want any category definition posts
            if topic['title'].startswith('About the %s category' % self.category):
                continue

            content = self.normalise_html(first_post['cooked'])

            article_url='/'.join([self.url,'t',topic['slug'],str(id)])

            # perhaps this article was imported from elsewhere by this class in
            # the past.
            meta = get_meta(content)

            kwargs = {
                'title':topic['title'],
                'url':article_url,
                'body':content,
                'username':first_post['username'],
                'pubdate':parse_date(first_post['created_at']),
            }

            # override as meta header knows best!
            kwargs.update(meta)

            self.articles.append(Article(**kwargs))

            for post in topic['post_stream']['posts'][1:]:
                self.comments.append(Comment(
                    body=self.normalise_html(post['cooked']),
                    article_url=article_url,
                    pubdate=parse_date(post['created_at']),
                    username=post['username'],
                ))
                self.usernames.add(post['username'])

        # get user profiles (cannot list emails)
        for username in self.usernames:
            p = self.get('users',username)["user"]
            self.user_profiles.append(UserProfile(
                    username=p["username"],
                    name=p["name"],
                    title=p["title"],
                    avatar=self.url+p["avatar_template"].format(size=200),
                    bio=p["bio_cooked"],
                    website=p["website"],
                    #invited_by=p["invited_by"]["username"] if p.get("invited_by") else None,
                    #attributes={}, # links to twitter, linkedin, etc
            ))

        self.crawled = True

    def publish(self,article):
        "Lazily publish/update an article. Only publish if A) local cache doesn't contain article at revision and B) nor does discourse"
        # TODO support updating

        if not self.crawled:
            raise RuntimeError('crawl() before publish()')

        # used to check if article has been posted already with something that
        # can roundtrip the discourse search
        canary = sha256(article.original_url+'canary').hexdigest()

        header = yaml.dump({
            'url':article.original_url,
            'revision':article.revision,
            'pubdate':article.pubdate,
            'username':article.username,
            'title':article.title,
        },default_flow_style=False)

        # will end up in pre/code tags so that this can be parsed from the
        # article body with get_meta
        # from raw body -- discourse will deal with the sanitisation.
        # TODO if there are problems -- excerpt will do.
        body = article_notice.format(
                site_name=config['site_name'],
                header=header,
                canary=canary,
                article=article.body,
            )

        # necessary hacks for proper display
        body.replace('<code>','\n```\n')
        body.replace('</code>','\n```\n')

        # already here?
        for existing in self.articles:
            if article.original_url == existing.original_url:
                return

        # from discourse in the first place (should have already been caught --
        # failsafe)
        if article.original_url.startswith(self.url):
            log.warn("Article %s discovered with prefix detection which means it wasn't in the category list on the API call.",article.original_url)
            return

        # look for a post containing the article original URL
        posts = self.get('search',q=canary)['posts']

        if len(posts):
            log.warn("Article %s discovered with canary detection which means it wasn't in the category list on the API call.",article.original_url)
            return

        # publish, it's not there!
        log.info('Publishing %s to discourse',article.original_url)

        self.post('posts',
            title='{0} -- {1}'.format(article.title,article.pubdate.strftime('%b/%d/%Y')),
            raw=body,
            category=self.category,
            )

