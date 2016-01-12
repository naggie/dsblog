from __future__ import division
import os
import re
from PIL import Image
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
from StringIO import StringIO

class Slugger():
    'Slugify with a memory: emit unique slugs'
    slugs = set()

    def __init__(self,initial=[]):
        self.slugs = set(initial)


    def slugify(self,resource):
        initial_slug = re.sub(r'([^\w\.]+|\.\.\. )','-',resource).strip('-').lower()

        count = 0
        slug = initial_slug
        while True:
            if slug not in self.slugs:
                self.slugs.add(slug)
                return slug

            count+=1
            # a file name? add a number before the first dot to be safe
            parts = list(os.path.splitext(initial_slug))
            parts[0] += '-%s' % count
            slug = ''.join(parts)


class Localizer():
    'Localise given remote URLs'
    # original URLS -> filesystem path
    remote_map = dict()

    # new URLS -> filesystem path
    local_map = dict()

    def __init__(self,local_dir,url):

        if not os.path.exists(local_dir):
            os.mkdir(local_dir)

        self.local_dir = local_dir
        self.url = url.strip('/')

        self.slugify = Slugger().slugify


    def localise(self,url):
        'return a new local URL for the given resource, deferring download'
        # data-url? already local
        if url.startswith('data'):
            return url

        if url in self.remote_map:
            return self.url+'/'+os.path.basename(self.remote_map[url])

        filename = self.slugify(url)
        filepath = os.path.join(self.local_dir,filename)

        new_url = self.url + '/' + filename

        self.remote_map[url] = filepath
        self.local_map[new_url] = filepath

        return new_url


    def localise_images(self,html):
        content = BeautifulSoup(html,'html.parser')
        for img in content.find_all('img'):
            img['src'] = self.localise(img["src"])

        return unicode(content)


    def download(self):
        "download all deferred resources if they don't already exist"

        for url,filepath in self.remote_map.items():
            if os.path.exists(filepath):
                del self.remote_map[url]

        if not self.remote_map:
            return

        print "Localising new images..."
        for url,filepath in tqdm(self.remote_map.items(),leave=True):
            try:
                r = requests.get(url, stream=True)
                if r.status_code == 200:
                    with open(filepath, 'wb') as f:
                        for chunk in r:
                            f.write(chunk)
                else:
                    for u,f in self.local_map.items():
                        if f == filepath:
                            del self.local_map[u]
            except requests.exceptions.ConnectionError:
                continue


    def annotate_images(self,html,max_width=710):
        'Add (scaled) width/height to images to prevent DOM reflow thrashing as images are loaded. RUN AFTER DOWNLOAD'
        soup = BeautifulSoup(html, 'html.parser')

        for img in soup.find_all('img'):
            if not img.get("width") or not img.get("height"):
                if img["src"].startswith('data'):
                    # data URI, deterministic as already loaded. No need.
                    return

                filepath = self.local_map[img["src"]]

                try:
                    image = Image.open(filepath)
                except IOError:
                    continue

                factor = min(max_width,image.width)/image.width
                img['width'] = int(image.width*factor)
                img['height'] = int(image.height*factor)

        return unicode(soup)


