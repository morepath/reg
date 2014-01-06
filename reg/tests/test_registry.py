from __future__ import unicode_literals
from reg.registry import Registry
from reg.lookup import Matcher, ComponentLookupError
import pytest


def test_registry_sources():
    reg = Registry()

    class Document(object):
        pass

    class SpecialDocument(Document):
        pass

    def linecount(obj):
        pass

    reg.register(linecount, [Document], 'document line count')
    reg.register(linecount, [SpecialDocument], 'special document line count')

    assert (reg.component(linecount, [Document()]) ==
            'document line count')

    assert (reg.component(linecount, [SpecialDocument()]) ==
            'special document line count')

    class AnotherDocument(Document):
        pass

    assert (reg.component(linecount, [AnotherDocument()]) ==
            'document line count')

    class Other(object):
        pass

    assert reg.component(linecount, [Other()], default=None) is None


def test_registry_target_find_specific():
    reg = Registry()

    class Document(object):
        pass

    class SpecialDocument(Document):
        pass

    def linecount(obj):
        pass

    def special_linecount(obj):
        pass

    reg.register(linecount, [Document], 'line count')
    reg.register(special_linecount, [Document], 'special line count')

    assert reg.component(linecount, [Document()]) == 'line count'
    assert (reg.component(special_linecount, [Document()]) ==
            'special line count')

    assert reg.component(linecount, [SpecialDocument()]) == 'line count'
    assert (reg.component(special_linecount, [SpecialDocument()]) ==
            'special line count')


# def test_registry_target_find_subclass():
#     reg = Registry()

#     class Document(object):
#         pass

#     class Animal(object):
#         pass

#     class Elephant(Animal):
#         pass

#     reg.register(Elephant, (Document,), 'elephant')
#     assert reg.component(Animal, (Document(),)) == 'elephant'


def test_registry_no_sources():
    reg = Registry()

    class Animal(object):
        pass

    def something():
        pass

    reg.register(something, (), 'elephant')
    assert reg.component(something, ()) == 'elephant'


def test_matcher():
    reg = Registry()

    class Document(object):
        def __init__(self, id):
            self.id = id

    def linecount(obj):
        pass

    class MyMatcher(Matcher):
        def __call__(self, doc):
            if doc.id == 1:
                return 'normal'
            else:
                return 'special'

    reg.register(linecount, [Document],
                 MyMatcher())

    assert reg.component(linecount, [Document(1)]) == 'normal'
    assert reg.component(linecount, [Document(2)]) == 'special'


def test_matcher_inheritance():
    reg = Registry()

    class Document(object):
        def __init__(self, id):
            self.id = id

    class SpecialDocument(Document):
        pass

    def linecount(obj):
        pass

    class DocumentMatcher(Matcher):
        def __call__(self, doc):
            if doc.id == 1:
                return 'normal'
            else:
                return 'special'

    class SpecialDocumentMatcher(Matcher):
        def __call__(self, doc):
            if doc.id == 2:
                return 'extra normal'
            else:
                return None

    reg.register(linecount, [Document],
                 DocumentMatcher())
    reg.register(linecount, [SpecialDocument],
                 SpecialDocumentMatcher())

    assert reg.component(linecount, [Document(1)]) == 'normal'
    assert reg.component(linecount, [Document(2)]) == 'special'
    assert reg.component(linecount, [SpecialDocument(1)]) == 'normal'
    assert reg.component(linecount, [SpecialDocument(2)]) == 'extra normal'
    assert reg.component(linecount, [SpecialDocument(3)]) == 'special'


def test_matcher_predicates():
    reg = Registry()

    class Document(object):
        pass

    class SpecialDocument(Document):
        pass

    def linecount(obj):
        pass

    count = {
        'predicates': 0,
        'called': 0
        }

    class DocumentMatcher(Matcher):
        def predicates(self, doc):
            count['predicates'] += 1
            return dict(precalculated=100)

        def __call__(self, doc, precalculated):
            count['called'] += 1
            return 'value: %s' % precalculated

    class SpecialDocumentMatcher(Matcher):
        def predicates(self, doc):
            count['predicates'] += 1
            return dict(precalculated=100)

        def __call__(self, doc, precalculated):
            count['called'] += 1
            return None

    reg.register(linecount, [Document],
                 DocumentMatcher())
    reg.register(linecount, [SpecialDocument],
                 SpecialDocumentMatcher())

    assert reg.component(linecount, [Document()]) == 'value: 100'
    assert count['called'] == 1
    assert count['predicates'] == 1
    assert reg.component(linecount, [SpecialDocument()]) == 'value: 100'
    # called two more times, but predicates only called once
    assert count['called'] == 3
    assert count['predicates'] == 2


def test_register_twice_with_sources():
    reg = Registry()

    class Document(object):
        pass

    def linecount(obj):
        pass

    reg.register(linecount, [Document], 'document line count')
    reg.register(linecount, [Document], 'another line count')
    assert reg.component(linecount, [Document()]) == 'another line count'


def test_register_twice_without_sources():
    reg = Registry()

    def linecount(obj):
        pass

    reg.register(linecount, [], 'once')
    reg.register(linecount, [], 'twice')
    assert reg.component(linecount, []) == 'twice'


def test_clear():
    reg = Registry()

    def linecount(obj):
        pass

    reg.register(linecount, [], 'once')
    assert reg.component(linecount, []) == 'once'
    reg.clear()
    with pytest.raises(ComponentLookupError):
        reg.component(linecount, [])


def test_exact():
    reg = Registry()

    class Document(object):
        pass

    class SubDocument(Document):
        pass

    def linecount(obj):
        pass

    def other(obj):
        pass

    reg.register(linecount, [Document], 'once')
    assert reg.exact(linecount, [Document]) == 'once'
    assert reg.exact(linecount, [SubDocument]) is None
    assert reg.exact(other, [Document]) is None

# XXX various default and component lookup error tests
