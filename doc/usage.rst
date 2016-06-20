Using Reg
=========

.. testsetup:: *

  pass

Introduction
------------

Reg lets you write `generic functions`_ that dispatch on some of their
arguments. To support this, Reg provides an implementation of
`multiple dispatch`_ in Python. Reg goes beyond dispatching on the
class of the arguments but can also dispatch on other aspects of
arguments.

In other words: Reg lets you define methods outside their classes as
plain Python functions. Reg in its basic use is like the single
dispatch implementation described in Python `PEP 443`_, but Reg
provides a lot more flexibility.

Reg supports loose coupling. You can define a function in your core
application or framework but provide implementations of this function
outside of it.

Reg gives developers fine control over how to find implemenations of
these functions. You can have multiple independent dispatch
registries. For special use cases you can also register and look up
other objects instead of functions.

What is Reg for? Reg offers infrastructure that lets you build more
powerful frameworks -- frameworks that can be extended and overridden
in a general way. The Morepath_ web framework is built on top of
Reg. Reg may seem like overkill to you. You may very well be right; it
depends on what you're building.

.. _`multiple dispatch`: http://en.wikipedia.org/wiki/Multiple_dispatch

.. _`generic functions`: https://en.wikipedia.org/wiki/Generic_function

.. _`PEP 443`: http://www.python.org/dev/peps/pep-0443/

.. _`Morepath`: http://morepath.readthedocs.io

Example
-------

Here is an example of Reg. First we define a generic function that
dispatches based on the class of its ``obj`` argument:

.. testcode::

  import reg
  @reg.dispatch('obj')
  def title(obj):
     return "we don't know the title"

Now we create a few example classes for which we want to be able to use
the ``title`` function we defined above.

.. testcode::

  class TitledReport(object):
     def __init__(self, title):
        self.title = title

  class LabeledReport(object):
     def __init__(self, label):
        self.label = label

In ``TitledReport`` there's an attribute called ``title`` but in the
``LabeledReport`` case we have an attribute ``label`` we want to use
as the title. We will implement this behavior in a few plain python
functions:

.. testcode::

  def titled_report_title(obj):
      return obj.title

  def labeled_report_title(obj):
      return obj.label

We now create a Reg :class:`reg.Registry`, and tell it about a few
implementations for the ``title`` function:

.. testcode::

  registry = reg.Registry()
  registry.register_function(
      title, titled_report_title, obj=TitledReport)
  registry.register_function(
      title, labeled_report_title, obj=LabeledReport)

We then tell Reg to use it automatically using
:meth:`reg.implicit.Implicit.initialize`:

.. testcode::

  from reg import implicit
  implicit.initialize(registry.lookup())

Once we've done this, our generic ``title`` function works on both
titled and labeled objects:

.. doctest::

  >>> titled = TitledReport('This is a report')
  >>> labeled = LabeledReport('This is also a report')
  >>> title(titled)
  'This is a report'
  >>> title(labeled)
  'This is also a report'

Our example is over, so we reset the implicit registry set up before:

.. testcode::

  implicit.clear()

Why not just use plain functions or methods instead of generic
functions? Often plain functions or methods will be the right
solution. But not always -- in this document we will examine a
situation where generic functions are useful.

Generic functions
=================

A Hypothetical CMS
------------------

Let's look at how Reg works in the context of a hypothetical content
management system (CMS).

This hypothetical CMS has two kinds of content item (we'll add more
later):

* a ``Document`` which contains some text.

* a ``Folder`` which contains a bunch of content entries, for instance
  ``Document`` instances.

This is the implementation of our CMS:

.. testcode::

  class Document(object):
     def __init__(self, text):
         self.text = text

  class Folder(object):
     def __init__(self, entries):
         self.entries = entries

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
     def __init__(self, entries):
         self.entries = entries

     def size(self):
         return sum([entry.size() for entry in self.entries])

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
the entries inside it are; if they have a ``size`` method that gives
the right result, it will work. If a new content item ``Image`` is
defined and we provide a ``size`` method for this, a ``Folder``
instance that contains ``Image`` instances will still be able to
calculate its size. Let's try this:

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
  >>> folder.entries.append(image)
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

  def document_size(item):
      return len(item.text)

  def folder_size(item):
      return sum([document_size(entry) for entry in item.entries])

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
``document_size``. It would fail when presented with a folder with an
``Image`` in it:

.. doctest::

  >>> folder_size(folder)
  Traceback (most recent call last):
    ...
  AttributeError: ...

To support ``Image`` we first need an ``image_size`` function:

.. testcode::

  def image_size(item):
     return len(item.bytes)

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

  def folder_size(item):
      return sum([size(entry) for entry in item.entries])

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

  def file_size(item):
      return len(item.bytes)

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

  def size(item):
      raise NotImplementedError

This function raises ``NotImplementedError`` as we don't know how to
get the size for an arbitrary Python object. Not very useful yet. We need
to be able to hook the actual implementations into it. To do this, we first
need to transform the ``size`` function to a generic one:

.. testcode::

  import reg
  size = reg.dispatch('item')(size)

We can actually spell these two steps in a single step, as
:func:`reg.dispatch` can be used as decorator:

.. testcode::

  @reg.dispatch('item')
  def size(item):
      raise NotImplementedError

We can now register the various size functions for the various content
items in a registry:

.. testcode::

  r = reg.Registry()
  r.register_function(size, document_size, item=Document)
  r.register_function(size, folder_size, item=Folder)
  r.register_function(size, image_size, item=Image)
  r.register_function(size, file_size, item=File)

We can now use our ``size`` function:

.. doctest::

  >>> size(doc, lookup=r.lookup())
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

  If your generic function implementation defines a ``lookup``
  argument it will receive the lookup used. This way you can continue
  passing the lookup along explicitly from generic function to generic
  function if you want to.

  It's annoying to have to keep spelling this out all the time -- we
  don't do it in our ``folder_size`` implementation, for instance, so
  that will fail too, even if we pass a lookup to the our ``size``
  function, as it won't be passed along implicitly.

  .. doctest::

    >>> size(folder, lookup=r.lookup())
    Traceback (most recent call last):
      ...
    NoImplicitLookupError: Cannot lookup without explicit lookup argument because no implicit lookup was configured.

Using :py:meth:`reg.implicit.Implicit.initialize` we can specify an
implicit lookup argument for all generic lookups so we don't have to
pass it in anymore:

.. testcode::

  from reg import implicit
  implicit.initialize(r.lookup())

Now we can just call our new generic ``size``:

.. doctest::

  >>> size(doc)
  12

And it will work for folder too:

.. doctest::

  >>> size(folder)
  25

It will work for subclasses too:

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

  @reg.dispatch('obj')
  def icon(obj):
      raise NotImplementedError

We can now register the ``DocumentIcon`` adapter class for this
function and ``Document``:

.. testcode::

  r.register_function(icon, DocumentIcon, obj=Document)

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

  r.register_function(icon, ImageIcon, obj=Image)

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

  @reg.dispatch('request', 'model')
  def view(request, model):
      raise NotImplementedError

We now define a concrete view for ``Document``:

.. testcode::

  def document_view(request, document):
      return "The document content is: " + document.text

Let's register the view in the registry:

.. testcode::

  r.register_function(view, document_view,
                      request=Request, model=Document)

We now see why the second argument to ``register()`` is a list; so far
we only supplied a single entry in it, but here we supply two, as we
have two parameters on which to do dynamic dispatch.

Given a request and a document, we can now call ``view``:

.. doctest::

  >>> request = Request()
  >>> view(request, doc)
  'The document content is: Hello world!'

Service Discovery
=================

Sometimes you want your application to have configurable services. The
application may for instance need a way to send email, but you don't
want to hardcode any particular way into your app, but instead leave
this to a particular deployment-specific configuration. You can use the Reg
infrastructure for this as well.

The simplest way to do this with Reg is by using a generic service lookup
function:

.. testcode::

  @reg.dispatch()
  def emailer():
      raise NotImplementedError

Here we've created a generic function that takes no arguments (and
thus does no dynamic dispatch). But it's still generic, so we can plug
in its actual implementation elsewhere, into the registry:

.. testcode::

  sent = []

  def send_email(sender, subject, body):
      # some specific way to send email
      sent.append((sender, subject, body))

  def actual_emailer():
      return send_email

  r.register_function(emailer, actual_emailer)

Now when we call emailer, we'll get the specific service we want:

.. doctest::

  >>> the_emailer = emailer()
  >>> the_emailer('someone@example.com', 'Hello', 'hello world!')
  >>> sent
  [('someone@example.com', 'Hello', 'hello world!')]

In this case we return the function ``send_email`` from the
``emailer()`` function, but we could return any object we want that
implements the service, such as an instance with a more extensive API.

replacing class methods
-----------------------

Reg generic functions can be used to replace methods, so that you can
follow the open/closed principle and add functionality to a class
without modifying it. This works for instance methods, but what about
``classmethod``? This takes the *class* as the first argument, not an
instance. You can configure ``@reg.dispatch`` decorator with a special
:class:`Predicate` instance that lets you dispatch on a class argument
instead of an instance argument.

Here's what it looks like:

.. testcode::

  @reg.dispatch(reg.match_class('cls', lambda cls: cls))
  def something(cls):
      raise NotImplementedError()

Note the call to :func:`match_class` here. This lets us specify that
we want to dispatch on the class, and we supply a lambda function that
shows how to extract this from the arguments to ``something``; in this
case we simply want the ``cls`` argument.

Let's use it:

.. testcode::

  def something_for_object(cls):
      return "Something for %s" % cls

  r.register_function(something, something_for_object, cls=object)

  class DemoClass(object):
      pass

When we now call ``something()`` with ``DemoClass`` as the first
argument we get the expected output:

.. doctest::

  >>> something(DemoClass)
  "Something for <class 'DemoClass'>"

This also knows about inheritance. So, you can write more specific
implementations for particular classes:

.. testcode::

  class ParticularClass(object):
      pass

  def something_particular(cls):
      return "Particular for %s" % cls

  r.register_function(something, something_particular,
                      cls=ParticularClass)

When we call ``something`` now with ``ParticularClass`` as the argument,
then ``something_particular`` is called:

.. doctest::

  >>> something(ParticularClass)
  "Particular for <class 'ParticularClass'>"

Lower level API
===============

Component lookup
----------------

You can look up the function that a function would dispatch to without
calling it. You do this using the ``component`` method on the dispatch
function:

.. doctest::

  >>> size.component(doc) is document_size
  True

Getting all
-----------

As we've seen, Reg supports inheritance. ``size`` for instance was
registered for ``Document`` instances, and is therefore also available
of instances of its subclass, ``HtmlDocument``:

.. doctest::

  >>> size.component(doc) is document_size
  True
  >>> size.component(htmldoc) is document_size
  True

Using the special ``all`` function we can also get an iterable of
*all* the components registered for a particular instance, including
those of base classes. Right now this is pretty boring as there's
only one of them:

.. doctest::

  >>> list(size.all(doc))
  [<function document_size at ...>]
  >>> list(size.all(htmldoc))
  [<function document_size at ...>]

We can make this more interesting by registering a special
``htmldocument_size`` to handle ``HtmlDocument`` instances:

.. testcode::

  def htmldocument_size(doc):
     return len(doc.text) + 1 # 1 so we can see a difference

  r.register_function(size, htmldocument_size,
                      item=HtmlDocument)

``size.all()`` for ``htmldoc`` now also gives back the more specific
``htmldocument_size``::

  >>> list(size.all(htmldoc))
  [<function htmldocument_size at ...>, <function document_size at ...>]

Using the Registry directly
---------------------------

The key under which we register something in a registry in fact doesn't
need to be a function. We can register predicate for any immutable key such
as a string:

.. testcode::

  r.register_predicates('some key', [reg.match_argname('obj')])

We can now register something for this key:

.. testcode::

  r.register_value('some key', [Document], 'some registered')

We can't get it at it using a generic dispatch function anymore
now. We can use the :class:`reg.Registry` API instead. Here's what to
do:

.. doctest::

  >>> r.component('some key', Document)
  'some registered'
  >>> list(r.all('some key', Document))
  ['some registered']

Caching
-------

We can turn a plain :class:`reg.Registry` into a faster, caching class
lookup using :class:`reg.CachingKeyLookup`:

.. doctest::

  >>> caching = reg.CachingKeyLookup(r, 100, 100, 100)

Turning it back into a lookup gives us a caching version of what we had
before:

.. doctest::

  >>> caching_lookup = caching.lookup()
  >>> size(doc, lookup=caching_lookup)
  12
  >>> size(doc, lookup=caching_lookup)
  12

You'll have to trust us on this, but it's faster the second time as
the dispatch to ``document_size`` was cached!
