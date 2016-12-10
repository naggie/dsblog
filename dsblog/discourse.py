# may factor into generic crawler interface + processor
import requests
from iso8601 import parse_date
from tqdm import tqdm
import re
from bs4 import BeautifulSoup

class Discourse():
    def __init__(self,url,api_user,api_key,category="Blog",extra_usernames=[]):
        super(Discourse,self).__init__(url)

        self.api_key = api_key
        self.api_user = api_user
        self.category = category

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
        for id in tqdm(ids,leave=True):
            topic = self.get('t',id)
            first_post = topic['post_stream']['posts'][0]

            self.usernames.add(first_post['username'])

            # don't want any category definition posts
            if topic['title'].startswith('About the %s category' % self.category):
                continue

            content = self.normalise_html(first_post['cooked'])

            comments = list()
            for post in topic['post_stream']['posts'][1:]:
                comments.append({
                    "content": self.normalise_html(post['cooked']),
                    "username": post['username'],
                })


            self.articles.append({
                "title":topic['title'],
                "url": '/'.join([self.url,'t',topic['slug'],str(id)]),
                "comments_url": '/'.join([self.url,'t',topic['slug'],str(id)]),
                "image": self.find_image(content),
                # fix internal image URLS which don't have protocol
                "content":content,
                "excerpt":self.generate_excerpt(content),
                "username":first_post["username"],
                "published":parse_date(first_post['created_at']),
                "comments":comments,
            })

        # get user profiles (cannot list emails)
        for username in self.usernames:
            p = self.get('users',username)["user"]
            self.user_profiles.append({
                    "username" : p["username"],
                    "name" : p["name"],
                    "avatar":self.url+p["avatar_template"].format(size=200),
                    "title" : p["title"],
                    "bio" : p["bio_cooked"],
                    "website" : p["website"],
                    "invited_by" : p["invited_by"]["username"] if p.get("invited_by") else None,
                    "attributes" : {}, # links to twitter, linkedin, etc
            })
