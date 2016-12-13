from bs4 import BeautifulSoup
from hashlib import sha256
from os.path import join,isfile,splitext
from environment import getConfig
import requests
import logging
from PIL import Image
import re

log = logging.getLogger(__name__)
config = getConfig()

# TODO some kind of automatic serialisation support:
# https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
# JSON (prettyprinted) is prefered so src can be under version control
# https://jsonpickle.github.io/ ? NOOO -- pyyaml does all of this!

# TODO automatic wrapping of images in anchor tabs for conditional link to original

# TODO embed some from the URL in the filename



def get_deterministic_filename(url):
    'Get a deterministic local filename given a URL.'
    text = re.sub(r'[^0-9a-zA-Z\.]+','-',url).lower()
    # a few very common fragments
    text = re.sub(r'^https?-','',text)
    text = re.sub(r'(img|image)s?-','',text)
    text = re.sub(r'uploads?-','',text)
    text = text.replace('content-','')
    text = text.replace('original-','')
    text = text.replace('optimized-','')
    text = text.replace('default-','')

    name = text[:50]+'-'+sha256(url).hexdigest()[:16]

    base,ext = splitext(text)

    # return sha256(url).hexdigest() + ext
    return name + ext


def download(url,filepath,lazy=True):
    if not isfile(filepath) or not lazy:
        log.info('downloading %s',url)
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in r:
                f.write(chunk)


class ArticleImage(object):
    def __init__(self,url,max_width=config['max_article_img_width']):
        self.original_url = url
        filename = get_deterministic_filename(url)

        self.filepath = join(config['original_img_dir'],filename)
        self.url = join(config['original_img_dir'],filename)
        self.width = None
        self.height = None

        self.scaled_filepath = join(config['scaled_img_dir'],filename)
        self.scaled_url = join(config['scaled_img_dir'],filename)
        self.scaled_width = None
        self.scaled_height = None

        self._max_width = max_width

    def process(self):
        download(self.original_url,self.filepath)
        img = Image.open(self.filepath)
        self.height = img.height
        self.width = img.width

        scaled_img = img

        if img.width > self._max_width and not isfile(self.scaled_filepath):
            log.info('resizing %s',self.original_url)
            scaled_img = scaled_img.resize(
                    (
                        self._max_width,
                        int(img.height*self._max_width/img.width)
                    ),Image.ANTIALIAS)

            scaled_img.save(self.scaled_filepath)

        self.scaled_height = scaled_img.height
        self.scaled_width = scaled_img.width


class Article(object):
    def __init__(self,body,username,url,pubdate,title='',full=True,guid=None):
        'Requires fully qualified image URLs and links. URL must also be fully qualified.'
        self.body = body # original, always
        self.title = title
        self.username = username
        self.url = url
        self.pubdate = pubdate
        self.full = full

        self.revision = hash(title+body)

        # ORDERED list of ArticleImage objects.
        self.images = list()
        # a map for easy lookup.
        self.image_map = dict()

        if not url.startswith('http'):
            raise ValueError('article url should be fully qualified')

        for anchor in BeautifulSoup(body,'html.parser').find_all('a'):
            if not anchor['href'].startswith('http'):
                raise ValueError('All links must be fully qualified. Offence: %s' % anchor['href'])

        for img in BeautifulSoup(body,'html.parser').find_all('img'):
            src = img['src']
            if not src.startswith('http'):
                raise ValueError('All images must be fully qualified. Offence: %s' % src)

            image = ArticleImage(src)
            self.images.append(image)
            self.image_map[src] = image


        self.images_processed = False


    def process(self):
        for image in self.images:
            image.process()

        self.images_processed = True

        self.header_img()


    def excerpt(self):
        'Generate an image-free excerpt'
        excerpt = unicode()
        content = BeautifulSoup(self.body,'html.parser')
        for p in content.find_all('p'):
            for img in p.find_all('img'):
                img.extract()

            excerpt += p.prettify(formatter="html")
            if len(excerpt) > 140:
                break

        return excerpt


    def compile_body(self):
        'Localise and annotate images + prettify HTML. Process images first.'

        if not self.images_processed:
            raise RuntimeError('Image not processed yet. Run process() method first to obtain images')

        soup = BeautifulSoup(self.body, 'html.parser')

        for img in soup.find_all('img'):
            if not img.get("width") or not img.get("height"):
                if img["src"].startswith('data'):
                    # data URI, deterministic as already loaded. No need.
                    return

                image = self.image_map[img['src']]
                img['src'] = image.scaled_url
                img['height'] = image.scaled_height
                img['width'] = image.scaled_width

                # TODO wrap wide images in link to original

        return soup.prettify(formatter="html")


    def header_img(self):
        'grab the local URL to a header image. Images must be processed first'

        if not self.images_processed:
            raise RuntimeError('Image not processed yet. Run process() method first to obtain images')

        for article_image in self.images:
            # not an emoji, avatar, etc.
            if article_image.width > 500:
                break
        else:
            return None


        header_filename = get_deterministic_filename(article_image.original_url)
        header_filepath = join(config['header_img_dir'],header_filename)
        header_url = join(config['header_img_dir'],header_filename)

        if not isfile(header_filepath):
            log.info('generating article header from %s',header_url)
            img = Image.open(article_image.filepath).resize((
                    config['max_article_img_width'],
                    int(article_image.height*config['max_article_img_width']/article_image.width)
                ),Image.ANTIALIAS)

            img = img.crop((
                0,
                int(article_image.height/2)-50,
                config['max_article_img_width'],
                int(article_image.height/2)+50,
            ))

            img.save(header_filepath)


        return header_url


class Comment(Article):
    def __init__(self,body,username,article_url,pubdate):

        super(Comment,self).__init__(
                body=body,
                username=username,
                url=article_url,
                pubdate=pubdate,
                full=True,
            )

        self.article_url = article_url
