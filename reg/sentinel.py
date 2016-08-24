class Sentinel(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return u'<%s>' % self.name


NOT_FOUND = Sentinel('NOT_FOUND')
