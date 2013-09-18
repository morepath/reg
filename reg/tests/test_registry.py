from reg.registry import Registry
from reg.interfaces import IMatcher


def test_registry_sources():
    reg = Registry()

    class Document(object):
        pass

    class SpecialDocument(Document):
        pass

    class LineCount(object):
        pass

    reg.register(LineCount, (Document,), 'document line count')
    reg.register(LineCount, (SpecialDocument,), 'special document line count')

    assert (reg.component(LineCount, (Document(),)) ==
            'document line count')

    assert (reg.component(LineCount, (SpecialDocument(),)) ==
            'special document line count')

    class AnotherDocument(Document):
        pass

    assert (reg.component(LineCount, (AnotherDocument(),)) ==
            'document line count')

    class Other(object):
        pass

    assert reg.component(LineCount, (Other(),), default=None) is None


def test_registry_target_find_specific():
    reg = Registry()

    class Document(object):
        pass

    class LineCount(object):
        pass

    class SpecialLineCount(LineCount):
        pass

    class SpecialDocument(Document):
        pass

    reg.register(LineCount, (Document,), 'line count')
    reg.register(SpecialLineCount, (Document,), 'special line count')

    assert reg.component(LineCount, (Document(),)) == 'line count'
    assert (reg.component(SpecialLineCount, (Document(),)) ==
            'special line count')

    assert reg.component(LineCount, (SpecialDocument(),)) == 'line count'
    assert (reg.component(SpecialLineCount, (SpecialDocument(),)) ==
            'special line count')


def test_registry_target_find_subclass():
    reg = Registry()

    class Document(object):
        pass

    class Animal(object):
        pass

    class Elephant(Animal):
        pass

    reg.register(Elephant, (Document,), 'elephant')
    assert reg.component(Animal, (Document(),)) == 'elephant'


def test_registry_no_sources():
    reg = Registry()

    class Animal(object):
        pass

    class Elephant(Animal):
        pass

    reg.register(Elephant, (), 'elephant')
    assert reg.component(Animal, ()) == 'elephant'


def test_matcher():
    reg = Registry()

    class Document(object):
        def __init__(self, id):
            self.id = id

    class LineCount(object):
        pass

    class SpecialLineCount(LineCount):
        pass

    class Matcher(IMatcher):
        def __init__(self, func, value):
            self.func = func
            self.value = value

        def __call__(self, *args, **kw):
            if self.func(*args, **kw):
                return self.value
            else:
                return None

    reg.register(LineCount, (Document,),
                 Matcher(lambda doc: doc.id == 1, 'line count'))

    reg.register(SpecialLineCount, (Document,),
                 Matcher(lambda doc: doc.id != 1, 'special line count'))

    assert reg.component(LineCount, (Document(1),)) == 'line count'
    assert reg.component(LineCount, (Document(2),)) == 'special line count'

# XXX various default and component lookup error tests
