from article import ArticleImage

class UserProfile():
    def __init__(self,username,name,title,avatar,bio,website):
        self.username = username
        self.name = name
        self.title = title
        self.avatar = ArticleImage(avatar)
        self.bio = bio
        self.website = website

        self.article_count = 0


    def process(self):
        self.avatar.process()

    # default ordering
    def __cmp__(self, other):
        return other.article_count - self.article_count
