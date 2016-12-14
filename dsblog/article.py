from __future__ import division
from bs4 import BeautifulSoup
from hashlib import sha256
from os.path import join,isfile,splitext
from environment import getConfig
import requests
import logging
from PIL import Image
from urlparse import urlparse
import re
from shutil import copyfile

log = logging.getLogger(__name__)
config = getConfig()

# TODO some kind of automatic serialisation support:
# https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
# JSON (prettyprinted) is prefered so src can be under version control
# https://jsonpickle.github.io/ ? NOOO -- pyyaml does all of this!

# TODO automatic wrapping of images in anchor tabs for conditional link to original

# TODO embed some from the URL in the filename

def remove_side_shadows(img):
    'remove the left and right drop shadows from an image, if grayscale'
    w,h = img.width,img.height
    max_clip = int(w/7)
    sample_height = int(h/10)

    y1 = int(h/2) - int(sample_height/2)
    y2 = int(h/2) + int(sample_height/2)

    # left
    # check for identical pixels in a column, stop when they change
    for left in range(1,max_clip):
        sample = img.crop((left,y1,left+1,y2)).convert('HSV')
        data = sample.getdata()
        # isn't grayscale
        if data[0][1] > 4:
            break

        # doesn't look like a line or shadow
        if len(set(data)) != 1:
            break



    return img.crop((left,0,w-left,h))


def dedup_list(l):
    'preserves order and dedup'
    ulist = list()
    [ulist.append(x) for x in l if x not in ulist]
    return ulist

def get_deterministic_filename(url):
    'Get a deterministic local filename given a URL.'
    text = re.sub(r'[^a-zA-Z\.]+','-',url).lower()
    # a few very common fragments
    text = re.sub(r'^https?-','',text)
    text = re.sub(r'(img|image)s?-','',text)
    text = re.sub(r'uploads?-','',text)
    text = text.replace('content-','')
    text = text.replace('original-','')
    text = text.replace('optimized-','')
    text = text.replace('default-','')
    text,ext = splitext(text)

    # remove repeated fragments
    text = '-'.join( dedup_list(text.split('-')) )

    name = text[:50]+'-'+sha256(url).hexdigest()[:16]


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
        self.url = join(config['original_img_url'],filename)
        self.width = None
        self.height = None

        self.scaled_filepath = join(config['scaled_img_dir'],filename)
        self.scaled_url = join(config['scaled_img_url'],filename)
        self.scaled_width = None
        self.scaled_height = None

        self._max_width = max_width

    def process(self):
        download(self.original_url,self.filepath)
        img = Image.open(self.filepath)
        self.height = img.height
        self.width = img.width

        if img.width > self._max_width:
            self.scaled_width = self._max_width
            self.scaled_height = int(img.height*self._max_width/img.width)

            if not isfile(self.scaled_filepath):
                log.info('resizing %s',self.original_url)
                scaled_img = img.resize(
                        (
                            self.scaled_width,
                            self.scaled_height,
                        ),Image.ANTIALIAS)

                scaled_img.save(self.scaled_filepath)
        else:
            self.scaled_height = self.height
            self.scaled_width = self.width

            if not isfile(self.scaled_filepath):
                copyfile(self.filepath,self.scaled_filepath)




class Article(object):
    def __init__(self,body,username,url,pubdate,title='',full=True,guid=None):
        'Requires fully qualified image URLs and links. URL must also be fully qualified.'
        self.body = body # original, always
        self.title = title
        self.username = username
        self.original_url = url
        self.origin = urlparse(url).netloc
        self.pubdate = pubdate
        self.full = full

        self.slug = re.sub(r'[^0-9a-zA-Z]+','-',title).lower()+'-'+sha256().hexdigest()[:6]

        self.url = '%s.html' % self.slug

        self.revision = hash(title+body)

        # ORDERED list of ArticleImage objects.
        self.images = list()
        # a map for easy lookup.
        self.image_map = dict()

        if not self.original_url.startswith('http'):
            raise ValueError('article url should be fully qualified')

        for anchor in BeautifulSoup(body,'html.parser').find_all('a'):
            if anchor.get('href') and not anchor['href'].startswith('http'):
                raise ValueError('All links must be fully qualified. Offence: %s' % anchor['href'])

        for img in BeautifulSoup(body,'html.parser').find_all('img'):
            src = img.get('src')

            if not src:
                return

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


    def compile_excerpt(self):
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
            # oh dear
            for article_image in self.images:
                if article_image.width > 250:
                    break
            else:
                return None


        header_filename = get_deterministic_filename(article_image.original_url)
        header_filepath = join(config['header_img_dir'],header_filename)
        header_url = join(config['header_img_url'],header_filename)

        if not isfile(header_filepath):
            log.info('generating article header from %s',article_image.original_url)
            img = Image.open(article_image.filepath)
            img = remove_side_shadows(img)
            img = img.resize((
                    config['max_article_img_width'],
                    int(article_image.height*config['max_article_img_width']/article_image.width)
                ),Image.ANTIALIAS)

            # -50 +50 around the center line
            img = img.crop((
                0,
                int(img.height/2)-50,
                config['max_article_img_width'],
                int(img.height/2)+50,
            ))

            img.save(header_filepath)


        return header_url

    # sorting a list of articles will sort by reverse pubdate.
    def __cmp__(self,other):
        return 1 if self.pubdate < other.pubdate else -1


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
