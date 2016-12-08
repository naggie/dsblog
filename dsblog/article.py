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
# https://jsonpickle.github.io/ ? NOOO -- pyyaml does all of this!


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

    def process(self):
        download(self.original_url,self.filepath)
        img = Image(self.filepath)
        self.height = img.height
        self.width = img.width

        scaled_img = img

        if img.width > config.DEFAULT_ARTICLE_IMAGE_WIDTH:
            scaled_img = scaled_img.resize(
                    (
                        config.DEFAULT_ARTICLE_IMAGE_WIDTH,
                        int(img.height*config.DEFAULT_ARTICLE_IMAGE_WIDTH/img.width)
                    ),Image.ANTIALIAS)

        self.scaled_height = scaled_img.height
        self.scaled_width = scaled_img.width


class Article():
    def __init__(self,body,title,username,url,pubdate,full=True,guid=None):
        'Requires fully qualified image URLs and links. URL must also be fully qualified.'
        self.body = body # original, always
        self.title = title
        self.username = username
        self.url = url
        self.pubdate = pubdate
        self.full = full
        self.guid = guid or url

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


    def process_images():
        for image in self.images:
            image.process()

        self.images_processed = False


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

        for image in self.images:
            # not an emoji, avatar, etc.
            if image.width > 500:
                break
        else:
            return None

        img = Image(image.filepath).resize((
                config.DEFAULT_ARTICLE_IMAGE_WIDTH,
                int(img.height*config.DEFAULT_ARTICLE_IMAGE_WIDTH/img.width
            )),Image.ANTIALIAS)

        img = img.crop((
            0,
            int(img.height/2)-50,
            config.DEFAULT_ARTICLE_IMAGE_WIDTH,
            int(img.height/2)+50,
        ))

        header_filename = get_deterministic_filename(image.original_url)
        header_filepath = join(config.HEADER_IMG_BASE_DIR,header_filename)
        header_url = join(config.HEADER_IMG_BASE_URL,header_filename)

        img.save(header_filepath)

        return header_url


