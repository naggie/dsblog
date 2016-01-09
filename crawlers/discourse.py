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

    def list_articles(self,name='Blog'):
        # find cetegory ID
        for cat in self.get(['categories'])['category_list']['categories']:
            id = cat['id']
            if name.lower() == cat['name'].lower():
                break
        else:
            raise IOError('Could not find category: %s'%name)

        # list topic IDs, collect usernames
        ids = list()
        for t in self.get(['c',id])['topic_list']['topics']:
            ids.append(t["id"])

        # don't want this
        category_definition_id = min(ids)
        ids.remove(category_definition_id)

        # load topics (containing posts: article then comments)
        #usernames = set()
            #usernames.add(t['username'])
        articles = list()
        for id in tqdm(ids,leave=True):
            topic = self.get(['t',id])
            first_post = topic['post_stream']['posts'][0]

            content = BeautifulSoup(first_post['cooked'],'html.parser')
            # repair all protocol-less URLS
            for img in content.find_all('img'):
                if img['src'].startswith('//'):
                    img['src'] = self.url.split('//')[0] + img['src']

            for a in content.find_all('a'):
                if a['href'].startswith('//'):
                    a['href'] = self.url.split('//')[0] + a['href']

            # remove useless meta links (a discourse-ism)
            for div in content.find_all('div',class_="meta"):
                div.extract()

            articles.append({
                "title":topic['title'],
                "url": '/'.join([self.url,'t',topic['slug'],str(id)]),
                #"image":"https://placeimg.com/710/100/tech",
                # fix internal image URLS which don't have protocol
                "content":unicode(content),
                "author_image":self.url+first_post["avatar_template"].format(size=200),
                "author_name":first_post["display_username"],
                "published":parse_date(first_post['created_at']),
            })

        return articles

