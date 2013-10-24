Using Reg
=========

.. testsetup:: *

  pass

Introduction
------------

Reg is an implementation of `multiple dispatch`_ in Python. Reg lets
you write methods outside their class as plain Python functions, and
methods that relate multiple classes at once.

XXX code sample

XXX talk about loose coupling

Reg gives developers fine control over how this dispatch works. For
special use cases you can register and look up other objects instead
of functions. You can have multiple independent dispatch registries,
and you can also compose them together.

With all this, Reg offers infrastructure that helps you build more
powerful registration APIs for your applications and frameworks. Reg
may seem like overkill to you. You may very well be right; it depends
on what you're building.

XXX pep 443

With Reg you can:

* call functions which have multiple implementations; which
  implementation gets called is based on the arguments you send in:
  single and multiple dispatch.

* provide a general way to look up and plug in services in your
  application: it supports a form of dependency injection.

* look up other objects registered for a set of arguments.

* look up a registered function or object according to other criteria
  (predicates).

* compose registries together, or isolate them.

.. _`multiple dispatch`: http://en.wikipedia.org/wiki/Multiple_dispatch

Generic functions
=================

A Hypothetical CMS
------------------

Let's look at how Reg works within the context of a hypothetical
content management system (CMS).

This hypothetical CMS has two kinds of content item (we'll add more
later):

* a ``Document`` which contains some text.

* a ``Folder`` which contains a bunch of content items, for instance
  ``Document`` instances.

This is the implementation of our CMS:

.. testcode::

  class Document(object):
     def __init__(self, text):
         self.text = text

  class Folder(object):
     def __init__(self, items):
         self.items = items

``size`` methods
----------------

Now we want to add a feature to our CMS: we want the ability to
calculate the size (in bytes) of any content item. The size of the
document is defined as the length of its text, and the size of the
folder is defined as the sum of the size of everything in it.

.. sidebar:: ``len(text)`` is not in bytes!

  Yeah, we're lying here. ``len(text)`` is not in bytes if text is in
  unicode. Just pretend that text is in ASCII only for the sake of
  this example, so that it's true.

If we have control over the implementation of ``Document`` and
``Folder`` we can implement this feature easily by adding a ``size``
method to both classes:

.. testcode::

  class Document(object):
     def __init__(self, text):
         self.text = text

     def size(self):
         return len(self.text)

  class Folder(object):
     def __init__(self, items):
         self.items = items

     def size(self):
         return sum([item.size() for item in self.items])

And then we can simply call the ``.size()`` method to get the size:

.. doctest::

  >>> doc = Document('Hello world!')
  >>> doc.size()
  12
  >>> doc2 = Document('Bye world!')
  >>> doc2.size()
  10
  >>> folder = Folder([doc, doc2])
  >>> folder.size()
  22

Note that the ``Folder`` size code is generic; it doesn't care what
the items inside it are; if they have a ``size`` method that gives the
right result, it will work. If a new content item ``Image`` is defined
and we provide a ``size`` method for this, a ``Folder`` instance that
contains ``Image`` instances will still be able to calculate its
size. Let's try this:

.. testcode::

  class Image(object):
      def __init__(self, bytes):
          self.bytes = bytes

      def size(self):
          return len(self.bytes)

When we add an ``Image`` instance to the folder, the size of the folder
can still be calculated:

.. doctest::

  >>> image = Image('abc')
  >>> folder.items.append(image)
  >>> folder.size()
  25

Adding ``size`` from outside
----------------------------

.. sidebar:: Open/Closed Principle

  The `Open/Closed principle`_ states software entities should be open
  for extension, but closed for modification. The idea is you may have
  a piece of software that you cannot or do not want to change, for
  instance because it's being developed by a third party, or because
  the feature you want to add is outside of the scope of that software
  (separation of concerns). By extending the software without
  modifying its source code, you can benefit from the stability of the
  core software and still add new functionality.

  .. _`Open/Closed principle`: https://en.wikipedia.org/wiki/Open/closed_principle

So far we didn't need Reg at all. But in the real world things may be
a lot more complicated. We may be dealing with a content management
system core where we *cannot* control the implementation of
``Document`` and ``Folder``. What if we want to add a size calculation
feature in an extension package?

We can fall back on good-old Python functions instead. We separate out
the size logic from our classes:

.. testcode::

  def document_size(document):
      return len(document.text)

  def folder_size(folder):
      return sum([document_size(item) for item in folder.items])

Generic size
------------

.. sidebar:: What about monkey patching?

  We *could* `monkey patch`_ a ``size`` method into all our content
  classes. This would work. But doing this can be risky -- what if the
  original CMS's implementers change it so it *does* gain a size
  method or attribute, for instance? Multiple monkey patches
  interacting can also lead to trouble. In addition, monkey-patched
  classes become harder to read: where is this ``size`` method coming
  from? It isn't there in the ``class`` statement, or in any of its
  superclasses! And how would we document such a construction?

  In short, monkey patching does not make for very maintainable code.

  .. _`monkey patch`: https://en.wikipedia.org/wiki/Monkey_patch

There is a problem with the above implementation however:
``folder_size`` is not generic anymore, but now depends on
``document_size``. It would fail when presented with a folder
with an ``Image`` in it:

.. doctest::

  >>> folder_size(folder)
  Traceback (most recent call last):
    ...
  AttributeError: ...

To support ``Image`` we first need an ``image_size`` function:

.. testcode::

  def image_size(image):
     return len(image.bytes)

We can now write a generic ``size`` function to get the size for any
item we give it:

.. testcode::

  def size(item):
      if isinstance(item, Document):
          return document_size(item)
      elif isinstance(item, Image):
          return image_size(item)
      elif isinstance(item, Folder):
          return folder_size(item)
      assert False, "Unknown item: %s" % item

With this, we can rewrite ``folder_size`` to use the generic ``size``:

.. testcode::

  def folder_size(folder):
      return sum([size(item) for item in folder.items])

Now our generic ``size`` function will work:

.. doctest::

  >>> size(doc)
  12
  >>> size(image)
  3
  >>> size(folder)
  25

All a bit complicated and hard-coded, but it works!

New ``File`` content
--------------------

What if we now want to write a new extension to our CMS that adds a
new kind of folder item, the ``File``, with a ``file_size`` function?

.. testcode::

  class File(object):
     def __init__(self, bytes):
         self.bytes = bytes

  def file_size(file):
      return len(file.bytes)

We would need to remember to adjust the generic ``size`` function so
we can teach it about ``file_size`` as well. Annoying, tightly
coupled, but sometimes doable.

But what if we are actually yet another party, and we have control of
neither the basic CMS *nor* its size extension? We cannot adjust
``generic_size`` to teach it about ``File`` now! Uh oh!

Perhaps the implementers of the size extension were wise and
anticipated this use case. They could have implemented
``size`` like this:

.. testcode::

  size_function_registry = {
     Document: document_size,
     Image: image_size,
     Folder: folder_size
  }

  def register_size(class_, function):
     size_function_registry[class_] = function

  def size(item):
     return size_function_registry[item.__class__](item)

We can now use ``register_size`` to teach ``size`` how to get
the size of a ``File`` instance:

.. testcode::

  register_size(File, file_size)

And it would work:

.. doctest::

  >>> size(File('xyz'))
  3

This is quite a bit of custom work on the parts of the implementers,
though. The API to manipulate the size registry is also completely
custom. But you can do it.

New ``HtmlDocument`` content
----------------------------

What if we introduce a new ``HtmlDocument`` item that is a subclass of
``Document``?

.. testcode::

  class HtmlDocument(Document):
      pass # imagine new html functionality here

Let's try to get its size:

.. doctest::

  >>> htmldoc = HtmlDocument('<p>Hello world!</p>')
  >>> size(htmldoc)
  Traceback (most recent call last):
     ...
  KeyError: ...

Uh oh, that doesn't work! There's nothing registered for the
``HtmlDocument`` class.

We need to remember to also call ``register_size`` for
``HtmlDocument``. We can reuse ``document_size``:

.. doctest::

  >>> register_size(HtmlDocument, document_size)

Now ``size`` will work:

.. doctest::

  >>> size(htmldoc)
  19

This is getting rather complicated, requiring not only foresight and
extra implementation work for the developers of ``size`` but also
extra work for the person who wants to subclass a content item.

Hey, we should write a system that generalizes this and automates a
lot of this, and gives us a more universal registry API, making our
life easier! And that's Reg.

Doing this with Reg
-------------------

Let's see how we could implement ``size`` using Reg.

First we need our generic ``size`` function:

.. testcode::

  def size(obj):
      raise NotImplementedError

This function raises ``NotImplementedError`` as we don't know how to
get the size for an arbitrary Python object. Not very useful yet. We need
to be able to hook the actual implementations into it. To do this, we first
need to transform the ``size`` function to a generic one:

.. testcode::

  import reg
  size = reg.generic(size)

We can actually spell these two steps in a single step, as
``generic`` can be used as decorator:

.. testcode::

  @reg.generic
  def size(obj):
      raise NotImplementedError

We can now register the various size functions for the various content
items in a registry:

.. testcode::

  r = reg.Registry()
  r.register(size, [Document], document_size)
  r.register(size, [Folder], folder_size)
  r.register(size, [Image], image_size)
  r.register(size, [File], file_size)

We can now use our ``size`` function:

.. doctest::

  >>> size(doc, lookup=r)
  12

.. sidebar:: The ``lookup`` argument

  What's this ``lookup`` argument about? It lets you specify explicitly
  what registry Reg looks in to look up the size functions, on our case
  ``r``.

  If we forget it, we'll get an error:

  .. doctest::

    >>> size(doc)
    Traceback (most recent call last):
      ...
    NoImplicitLookupError: Cannot lookup without explicit lookup argument because no implicit lookup was configured.

  It's annoying to have to keep spelling this out all the time -- we
  don't do it in our ``folder_size`` implementation, for instance, so
  that will fail too, even if we pass a lookup to the our ``size``
  function, as it won't be passed along implicitly.

  .. doctest::

    >>> size(folder, lookup=r)
    Traceback (most recent call last):
      ...
    NoImplicitLookupError: Cannot lookup without explicit lookup argument because no implicit lookup was configured.

We can specify an implicit lookup argument for all generic lookups so
we don't have to pass it in anymore:

.. testcode::

  from reg import implicit
  implicit.initialize(r)

Now we can just call our new generic ``size``:

.. doctest::

  >>> size(doc)
  12

And it will work for folder too:

.. doctest::

  >>> size(folder)
  25

It will work for subclasses too::

.. doctest::

  >>> size(htmldoc)
  19

Reg knows that ``HtmlDocument`` is a subclass of ``Document`` and will
find ``document_size`` automatically for you. We only have to register
something for ``HtmlDocument`` if we would want to use a special,
different size function for ``HtmlDocument``.

Using classes
-------------

The previous example worked well for a single function to get the
size, but what if we wanted to add a feature that required multiple
methods, not just one?

Let's imagine we have a feature to get the icon for a content object
in our CMS, and that this consists of two methods, with a way to get a
small icon and a large icon. We want this API:

.. testcode::

  from abc import ABCMeta, abstractmethod

  class Icon(object):
      __metaclass__ = ABCMeta
      @abstractmethod
      def small(self):
          """Get the small icon."""

      @abstractmethod
      def large(self):
          """Get the large icon."""

.. sidebar:: abc module?

  We've used the standard Python `abc module`_ to set the API in
  stone. But that's just a convenient standard way to express it. The
  ``abc`` module is not in any way required by Reg. You don't need to
  implement the API in a base class either. We just do it in this
  example to be explicit.

  .. _`abc module`: http://docs.python.org/2/library/abc.html

Let's implement the ``Icon`` API for ``Document``:

.. testcode::

  def load_icon(path):
      return path # pretend we load the path here and return an image obj

  class DocumentIcon(Icon):
     def __init__(self, document):
        self.document = document

     def small(self):
        if not self.document.text:
            return load_icon('document_small_empty.png')
        return load_icon('document_small.png')

     def large(self):
        if not self.document.text:
            return load_icon('document_large_empty.png')
        return load_icon('document_large.png')

The constructor of ``DocumentIcon`` receives a ``Document`` instance
as its first argument. The implementation of the ``small`` and
``large`` methods uses this instance to determine what icon to produce
depending on whether the document is empty or not.

We can call ``DocumentIcon`` an adapter, as it adapts the original
``Document`` class to provide an icon API for it. We can use it
manually:

.. doctest::

  >>> icon_api = DocumentIcon(doc)
  >>> icon_api.small()
  'document_small.png'
  >>> icon_api.large()
  'document_large.png'

But we want to be able to use the ``Icon`` API in a generic way, so let's
create a generic function that gives us an implementation of ``Icon`` back for
any object:

.. testcode::

  @reg.generic
  def icon(obj):
      raise NotImplementedError

We can now register the ``DocumentIcon`` adapter class for this
function and ``Document``:

.. testcode::

  r.register(icon, [Document], DocumentIcon)

We can now use the generic ``icon`` to get ``Icon`` API for a
document:

.. doctest::

  >>> api = icon(doc)
  >>> api.small()
  'document_small.png'
  >>> api.large()
  'document_large.png'

We can also register a ``FolderIcon`` adapter for ``Folder``, a
``ImageIcon`` adapter for ``Image``, and so on. For the sake of
brevity let's just define one for ``Image`` here:

.. testcode::

  class ImageIcon(Icon):
      def __init__(self, image):
          self.image = image

      def small(self):
          return load_icon('image_small.png')

      def large(self):
          return load_icon('image_large.png')

  r.register(icon, [Image], ImageIcon)

Now we can use ``icon`` to retrieve the ``Icon`` API for any item in
the system for which an adapter was registered:

.. doctest::

  >>> icon(doc).small()
  'document_small.png'
  >>> icon(doc).large()
  'document_large.png'
  >>> icon(image).small()
  'image_small.png'
  >>> icon(image).large()
  'image_large.png'

Multiple dispatch
------------------

Sometimes we want to adapt more than one thing at the time. The
canonical example for this is a web view lookup system. Given a
request and a model, we want to find a view that represents these. The
view needs to get the request, for parameter information, POST body,
URL information, and so on. The view also needs to get the model, as
that is what will be represented in the view.

You want to be able to vary the view depending on the type of the request
as well as the type of the model.

Let's imagine we have a ``Request`` class:

.. testcode::

  class Request(object):
      pass

We'll use ``Document`` as the model class.

We want a generic ``view`` function that given a request and a model
generates content for it:

.. testcode::

  @reg.generic
  def view(request, model):
      raise NotImplementedError

We now define a concrete view for ``Document``:

.. testcode::

  def document_view(request, document):
      return "The document content is: " + document.text

Let's register the view in the registry:

.. testcode::

  r.register(view, [Request, Document], document_view)

We now see why the second argument to ``register()`` is a list; so far
we only supplied a single entry in it, but here we supply two, as we
have two parameters on which to do dynamic dispatch.

Given a request and a document, we can now adapt it to ``IView``:

.. doctest::

  >>> request = Request()
  >>> view(request, doc)
  'The document content is: Hello world!'
