from crawler import Crawler
import feedparser
from time import mktime
from datetime import datetime
import pytz

class Hexo(Crawler):
    def __init__(self,url,user_email):
        super(Hexo,self).__init__()

        self.url = url
        self.user_email = user_email

    def crawl(self):
        d = feedparser.parse(self.url)

        for entry in d["entries"]:
            self.articles.append({
                "title":entry['title'],
                "url": entry["link"],
                "comments_url": entry['link'],
                "image": self.find_image(entry["summary"]),
                # fix internal image URLS which don't have protocol
                "content":entry["summary"],
                "author_image":"",
                "author_name":"",
                "published": pytz.utc.localize(datetime.fromtimestamp(mktime(entry["published_parsed"]))),
                "comments":[],
            })

