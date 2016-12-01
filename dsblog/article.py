from bs4 import BeautifulSoup
from hashlib import sha256
from os.path import join,isfile
import splitext
import config
import requests
import logging

log = logging.getLogger(__name__)

# TODO some kind of automatic serialisation support:
# https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
# JSON (prettyprinted) is prefered so src can be under version control
# https://jsonpickle.github.io/ ?

def get_deterministic_filename(img_url):
    'Get a deterministic local filename given a URL.'
    base,ext = splitext(img_url)

    return sha256(img_url).hexdigest() + ext


def download(url,filepath):
    r = requests.get(url, stream=True)
    t.raise_for_status()
    with open(filepath, 'wb') as f:
        for chunk in r:
            f.write(chunk)

class Article():
    def __init__(self,body,title,username,origin,pubdate,guid=None):
        'Requires fully qualified image URLs and links. URL must also be fully qualified.'
        self.body = body # original, always
        self.title = title
        self.username = username
        self.origin = origin
        self.pubdate = pubdate

        self.guid = guid or origin

        self.revision = hash(title+body)


        # set of original URL to local filepath and new URL
        self.img_url_map = set()

        if not origin.startswith('http'):
            raise ValueError('origin should be a fully qualified URL')

        for anchor in BeautifulSoup(body,'html.parser').find_all('a'):
            if not anchor['href'].startswith('http'):
                raise ValueError('All links must be fully qualified. Offence: %s' % anchor['href'])

        for img in BeautifulSoup(body,'html.parser').find_all('img'):
            src = img['src']
            if not src.startswith('http'):
                raise ValueError('All images must be fully qualified. Offence: %s' % src)


            filename = get_deterministic_filename(src)
            local_path = join(config.IMG_BASE_DIR,filename)
            new_url = join(config.IMG_BASE_URL,filename)

            self.img_url_map.add((src,local_path,new_url))


    def download_images():
        for original_url,filepath,new_url in self.img_url_map:
            if not isfile(filepath):
                log.info('downloading %s',original_url)
                download(original_url,filepath)


    def excerpt(self):
        excerpt = unicode()
        content = BeautifulSoup(self.body,'html.parser')
        for p in content.find_all('p'):
            for img in p.find_all('img'):
                img.extract()

            excerpt += p.prettify(formatter="html")
            if len(excerpt) > 140:
                break

        return excerpt

    def header_image(self):
        'Return a local URL to a header image'
        pass

    def localised_body(self):
        pass

    def _download_images(self):
        pass

    def _find_first_image_url(self):
        'look for best image URL or None, for header image'
        content = BeautifulSoup(self.body,'html.parser')
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

