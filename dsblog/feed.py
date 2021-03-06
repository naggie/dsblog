from article import Article
import feedparser
from time import mktime
from datetime import datetime
import pytz


def crawl(url,username,full_articles=True):
    articles = list()
    d = feedparser.parse(url)


    for entry in d["entries"]:
        if 'published_parsed' in entry:
            pubdate = pytz.utc.localize(datetime.fromtimestamp(mktime(entry['published_parsed'])))
        else:
            pubdate = pytz.utc.localize(datetime.fromtimestamp(mktime(entry['updated_parsed'])))

        articles.append(Article(
            title=entry['title'],
            url= entry['link'],
            body=entry["content"][0]["value"] if 'content' in entry else entry["summary"],
            username=username,
            pubdate=pubdate,
        ))

    return articles
