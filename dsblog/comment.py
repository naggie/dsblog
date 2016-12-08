from article import Article
# could share common parent with article. Very similar!


class Comment(Article):
    def __init__(self,body,username,article_url,pubdate):

        super(Comment,self).__init__(
                body=body,
                title=None,
                username=username,
                url=article_url,
                pubdate=pubdate,
                full=True,
                guid=article_url+'#'+pubdate.isoformat(),
            )
