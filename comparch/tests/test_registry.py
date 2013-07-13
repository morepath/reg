import py.test
from comparch.registry import Registry

def test_registry_sources():
    reg = Registry()
    
    class Document(object):
        pass

    class SpecialDocument(Document):
        pass

    class LineCount(object):
        pass

    reg.register(LineCount, (Document,), None,
                 'document line count')
    reg.register(LineCount, (SpecialDocument,), None,
                 'special document line count')

    assert (reg.lookup(LineCount, (Document(),),  None) ==
            'document line count')
    
    assert (reg.lookup(LineCount, (SpecialDocument(),), None) ==
            'special document line count')

    class AnotherDocument(Document):
        pass

    assert (reg.lookup(LineCount, (AnotherDocument(),), None) ==
            'document line count')
                           
    class Other(object):
        pass
    
    assert reg.lookup(LineCount, (Other(),), None) is None

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
    
    reg.register(LineCount, (Document,), None, 'line count')
    reg.register(SpecialLineCount, (Document,), None, 'special line count')

    assert reg.lookup(LineCount, (Document(),), None) == 'line count'
    assert reg.lookup(SpecialLineCount, (Document(),), None) == 'special line count'

    assert reg.lookup(LineCount, (SpecialDocument(),), None) == 'line count'
    assert reg.lookup(SpecialLineCount, (SpecialDocument(),), None) == 'special line count'

def test_registry_target_find_subclass():
    reg = Registry()

    class Document(object):
        pass

    class Animal(object):
        pass

    class Elephant(Animal):
        pass
    
    reg.register(Elephant, (Document,), None, 'elephant')
    assert reg.lookup(Animal, (Document(),), None) == 'elephant'

def test_registry_no_sources():
    reg = Registry()

    class Animal(object):
        pass

    class Elephant(Animal):
        pass
    
    reg.register(Elephant, (), None, 'elephant')
    assert reg.lookup(Animal, (), None) == 'elephant'
    
