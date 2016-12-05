from bs4 import BeautifulSoup
from hashlib import sha256
from os.path import join,isfile,splitext
import config
import requests
import logging
from PIL import Image

log = logging.getLogger(__name__)

# TODO some kind of automatic serialisation support:
# https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
# JSON (prettyprinted) is prefered so src can be under version control
# https://jsonpickle.github.io/ ?


def get_deterministic_filename(img_url):
    'Get a deterministic local filename given a URL.'
    base,ext = splitext(img_url)

    return sha256(img_url).hexdigest() + ext


def download(url,filepath,lazy=True):
    if not isfile(filepath) or not lazy:
        log.info('downloading %s',original_url)
        r = requests.get(url, stream=True)
        t.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in r:
                f.write(chunk)


class ArticleImage():
    def __init__(self,url):
        self.original_url = url
        filename = get_deterministic_filename(url)

        self.filepath = join(config.ORIGINAL_IMG_BASE_DIR,filename)
        self.url = join(config.ORIGINAL_IMG_BASE_URL,filename)
        self.width = None
        self.height = None

        self.scaled_filepath = join(config.SCALED_IMG_BASE_DIR,filename)
        self.scaled_url = join(config.ORIGINAL_IMG_BASE_URL,filename)
        self.scaled_width = None
        self.scaled_height = None

    def download(self):
        download(self.original_url,self.filepath)
        img = Image(self.filepath)
        self.height = img.height
        self.width = img.width

        scaled_img = img

        if img.width > config.DEFAULT_IMAGE_WIDTH:
            scaled_img = scaled_img.resize(
                    (
                        config.DEFAULT_IMAGE_WIDTH,
                        int(img.height*config.DEFAULT_IMAGE_WIDTH/img.width)
                    ),Image.ANTIALIAS)

        self.scaled_height = scaled_img.height
        self.scaled_width = scaled_img.width


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

        self.first_img_url = self._find_first_image_url()

        # set of original URL to local filepath and new URL
        self.images = list()

        if not origin.startswith('http'):
            raise ValueError('origin should be a fully qualified URL')

        for anchor in BeautifulSoup(body,'html.parser').find_all('a'):
            if not anchor['href'].startswith('http'):
                raise ValueError('All links must be fully qualified. Offence: %s' % anchor['href'])

        for img in BeautifulSoup(body,'html.parser').find_all('img'):
            src = img['src']
            if not src.startswith('http'):
                raise ValueError('All images must be fully qualified. Offence: %s' % src)


            self.images.append(ArticleImage(src))


    def download_images():
        for image in self.images:
            image.download()


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


    def localised_body(self):
        body = self.body

        for original_url,local_path,new_url in self.img_url_map:
            # could use BeautifulSoup instead in case image URLs are hacked!
            body = body.replace(original_url,new_url)

        return body

    def header_img(self):
        'grab the local URL to a header image. Images must be downloaded first'
        for image in self.images:
            if image.width > 500:
                break
        else:
            return None

        img = Image(image.filepath).resize((
                config.DEFAULT_IMAGE_WIDTH,
                int(img.height*config.DEFAULT_IMAGE_WIDTH/img.width
            )),Image.ANTIALIAS)

        img = img.crop((
            0,
            int(img.height/2)-50,
            config.DEFAULT_IMAGE_WIDTH,
            int(img.height/2)+50,
        ))

        header_filename = get_deterministic_filename(original_url)
        header_filepath = join(config.HEADER_IMG_BASE_DIR,header_filename)
        header_url = join(config.HEADER_IMG_BASE_URL,header_filename)

        img.save(header_filepath)

        return header_url
