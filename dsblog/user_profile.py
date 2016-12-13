from article import ArticleImage

class UserProfile():
    def __init__(self,username,name,title,avatar,bio,website):
        self.username = username
        self.name = name
        self.title = title
        self.avatar = ArticleImage(avatar)
        self.bio = bio
        self.website = website


    def process(self):
        self.avatar.process()
