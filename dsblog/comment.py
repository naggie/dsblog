from article import Article


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
