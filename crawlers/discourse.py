# may factor into generic crawler interface + processor
import requests
from iso8601 import parse_date
from tqdm import tqdm
import re
from bs4 import BeautifulSoup

class Discourse():
    def __init__(self,url,api_user,api_key):
        self.url = url.strip('/')
        self.api_key = api_key
        self.api_user = api_user

    def get(self,path):
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

        return unicode(content)


    def find_image(self,html):
        'look for best image URL or None, for header image'
        content = BeautifulSoup(html,'html.parser')
        image = None
        for img in content.find_all('img'):
            try:
                if 'emoji' in img['class'] or 'avatar' in img['class']:
                    continue
            except KeyError:
                pass

            image = img['src']
            break

        return image


    def list_articles(self,name='Blog'):
        # find cetegory ID
        for cat in self.get(['categories'])['category_list']['categories']:
            id = cat['id']
            if name.lower() == cat['name'].lower():
                self.cat_name = cat['name']
                break
        else:
            raise IOError('Could not find category: %s'%name)

        # list topic IDs, collect usernames
        ids = list()
        for t in self.get(['c',id])['topic_list']['topics']:
            ids.append(t["id"])


        # load topics (containing posts: article then comments)
        #usernames = set()
            #usernames.add(t['username'])
        articles = list()
        for id in tqdm(ids,leave=True):
            topic = self.get(['t',id])
            first_post = topic['post_stream']['posts'][0]

            # don't want any category definition posts
            if topic['title'].startswith('About the %s category' % self.cat_name):
                continue

            content = self.normalise_html(first_post['cooked'])

            comments = list()
            for post in topic['post_stream']['posts'][1:]:
                comments.append({
                    "content": self.normalise_html(post['cooked']),
                    "author_name": post['display_username'],
                    "author_image": self.url+post["avatar_template"].format(size=200),
                })


            articles.append({
                "title":topic['title'],
                "url": '/'.join([self.url,'t',topic['slug'],str(id)]),
                "comments_url": '/'.join([self.url,'t',topic['slug'],str(id)]),
                "image": self.find_image(content),
                # fix internal image URLS which don't have protocol
                "content":content,
                "author_image":self.url+first_post["avatar_template"].format(size=200),
                "author_name":first_post["display_username"],
                "published":parse_date(first_post['created_at']),
                "comments":comments,
            })

        return articles

