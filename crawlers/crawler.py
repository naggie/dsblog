from bs4 import BeautifulSoup

class Crawler():
    articles = list()
    users = dict()

    def crawl(self):
        raise NotImplementedError()

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
