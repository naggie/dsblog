# may factor into generic crawler interface + processor
import requests
from iso8601 import parse_date
import re
from bs4 import BeautifulSoup
import logging
from article import Article,Comment
from user_profile import UserProfile

# TODO read article header
# TODO publish articles
# TODO write article header

log = logging.getLogger(__name__)

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

    def get(self,*path):
        'get an API URL where list path is transformed into a JSON request and parsed'

        path = [str(p) for p in path]

        parts = [self.url] + path
        url = '/'.join(parts) + '.json'

        response = requests.get(
                url,
                params={
                    'api_user':self.api_user,
                    'api_key':self.api_key,
                }
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

            for post in topic['post_stream']['posts'][1:]:
                self.comments.append(Comment(
                    body=self.normalise_html(post['cooked']),
                    article_url=article_url,
                    pubdate=parse_date(post['created_at']),
                    username=post['username'],
                ))
                self.usernames.add(post['username'])


            self.articles.append(Article(
                title=topic['title'],
                url=article_url,
                body=content,
                username=first_post['username'],
                pubdate=parse_date(first_post['created_at']),
            ))

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

    def publish(self,article):
        "Lazily publish an article. Only publish if A) local cache doesn't contain article at revision and B) nor does discourse"
        pass
