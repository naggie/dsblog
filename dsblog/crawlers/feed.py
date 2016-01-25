from crawler import Crawler
import feedparser
from time import mktime
from datetime import datetime
import pytz

class Feed(Crawler):
    def __init__(self,url,username):
        super(Feed,self).__init__(url)
        self.username = username

    def crawl(self):
        d = feedparser.parse(self.url)

        for entry in d["entries"]:
            if 'content' in entry:
                content = entry["content"][0]["value"]
                full_article = True
            else:
                content = entry["summary"]
                full_article = False

            self.articles.append({
                "title":entry['title'],
                "url": entry["link"],
                "content":content if full_article else None,
                # still run through excerpt generator to remove images if they exist
                "excerpt": self.generate_excerpt(content),
                "username":self.username,
                "comments_url": entry['link'],
                "image": self.find_image(content),
                # fix internal image URLS which don't have protocol
                "published": pytz.utc.localize(datetime.fromtimestamp(mktime(entry["published_parsed"]))),
                "comments":[],
            })

