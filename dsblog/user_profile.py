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
        if not isinstance(other,self.__class__):
            return 0

        return other.article_count - self.article_count


class AnonymousUserProfile(UserProfile):
    def __init__(self):
        self.username = 'anonymous'
        self.name = 'Anonymous'
        self.title = 'Generic User'
        #self.avatar = ArticleImage()
        self.bio = 'Nothing to see here, move along...'
        self.website = None
        self.avatar = None

        self.article_count = 0

