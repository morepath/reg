from __future__ import unicode_literals
class Sentinel(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<%s>' % self.name
