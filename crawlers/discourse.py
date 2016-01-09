# may factor into generic crawler interface + processor
import requests

class Discourse():
    def __init__(self,url,api_user,api_key):
        self.url = url.strip('/')
        self.api_key = api_key
        self.api_user = api_user

    def get(self,path):
        'get an API URL where list path is transformed into a JSON request and parsed'

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

    #def list_category(name='Blog'):
    def list_category(self,name='Facility Automation'):
        for cat in self.get(['categories'])['category_list']['categories']:
            id = cat['id']
            if name.lower() == cat['name'].lower():
                break
        else:
            raise IOError('Could not find category: %s'%name)

        print id


import os
Discourse(
    url="http://localhost:8099",
    api_user="naggie",
    api_key=os.environ['API_KEY'],
).list_category()

