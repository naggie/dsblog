import feedparser
from time import mktime
from datetime import datetime
import pytz

class Feed():
    def __init__(self,url,username,full_articles=True):
        self.username = username

    def crawl(self):
        d = feedparser.parse(self.url)

        for entry in d["entries"]:
            if 'content' in entry:
                content = entry["content"][0]["value"]
            else:
                content = entry["summary"]

            self.articles.append({
                "title":entry['title'],
                "url": entry["link"],
                "content":content,
                # still run through excerpt generator to remove images if they exist
                "username":self.username,
                "comments_url": None,# entry['link'],
                # fix internal image URLS which don't have protocol
                "published": pytz.utc.localize(datetime.fromtimestamp(mktime(entry["published_parsed"]))),
                "comments":[],
            })

