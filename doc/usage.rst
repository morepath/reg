Using Reg
=========

.. testsetup:: *

  pass

Introduction
------------

Reg lets you write `generic functions`_.  To support this, Reg
provides an implementation of `multiple dispatch`_ in Python. Reg lets
you define methods outside their classes as plain Python
functions. Reg in its basic use is like the single dispatch
implementation described in Python `PEP 443`_, but Reg provides a lot
more flexibility.

Reg supports loose coupling. You can define a function in your core
application or framework but provide definitions of this function
outside of it.

Reg gives developers fine control over how to find implemenations of
these functions. You can have multiple independent dispatch
registries, and you can also compose them together. For special use
cases you can also register and look up other objects instead of
functions.

What is Reg for? Reg offers infrastructure that lets you build more
powerful frameworks -- frameworks that can be extended and overridden
in a general way. Reg may seem like overkill to you. You may very well
be right; it depends on what you're building.

.. _`multiple dispatch`: http://en.wikipedia.org/wiki/Multiple_dispatch

.. _`generic functions`: https://en.wikipedia.org/wiki/Generic_function

.. _`PEP 443`: http://www.python.org/dev/peps/pep-0443/

Example
-------

Here is an example of Reg. First we define a generic function:

.. testcode::

  import reg
  @reg.generic
  def title(obj):
     return "we don't know the title"

We now create a few example classes. We want to be able to get the title
for both.

.. testcode::

  class TitledReport(object):
     def __init__(self, title):
        self.title = title

  class LabeledReport(object):
     def __init__(self, label):
        self.label = label

In one case there's an attribute called ``title`` but in the
other case we have an attribute ``label`` we want to use as the title. We
will implement this behavior in a few plain python functions:

.. testcode::

  def titled_report_title(obj):
      return obj.title

  def labeled_report_title(obj):
      return obj.label

We now create a Reg :class:`reg.Registry`, register our
implementations in it using :meth:`reg.IRegistry.register`, and then
tell Reg to use it automatically using :meth:`reg.implicit.Implicit.initialize`:

.. testcode::

  registry = reg.Registry()
  registry.register(title, [TitledReport], titled_report_title)
  registry.register(title, [LabeledReport], labeled_report_title)
  from reg import implicit
  implicit.initialize(registry)

Once we've done this, our generic ``title`` function works both both
titled and labeled objects:

.. doctest::

  >>> titled = TitledReport('titled')
  >>> labeled = LabeledReport('labeled')
  >>> title(titled)
  'titled'
  >>> title(labeled)
  'labeled'

Our example is over, so we reset the implicit registry set up before:

.. testcode::

  implicit.clear()

Why not just use plain functions or methods instead of generic
functions? Often plain functions or methods will be the right solution.
But not always -- in this document we will motivate a case where
generic functions are useful.

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
:func:`reg.generic` can be used as decorator:

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

Using :py:meth:`reg.implicit.Implicit.initialize` we can specify an
implicit lookup argument for all generic lookups so we don't have to
pass it in anymore:

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

  @reg.generic
  def emailer():
      raise NotImplementedError

Here we've create a generic function that takes no arguments (and thus does
no dynamic dispatch). But it's still generic, so we can plug in its actual
implementation elsewhere, into the registry:

.. testcode::

  sent = []

  def send_email(sender, subject, body):
      # some specific way to send email
      sent.append((sender, subject, body))

  def actual_emailer():
      return send_email

  r.register(emailer, [], actual_emailer)

Now when we call emailer, we'll get the specific service we want:

.. doctest::

  >>> the_emailer = emailer()
  >>> the_emailer('someone@example.com', 'Hello', 'hello world!')
  >>> sent
  [('someone@example.com', 'Hello', 'hello world!')]

In this case we return the function ``send_email`` from the
``emailer()`` function, but we could return any object we want that
implements the service, such as an instance with a more extensive API.

Lower level API
===============

Registering non-functions
-------------------------

Some special use cases require the registration of other objects besides
callables. Reg exposes an API to get at these:

.. testcode::

  @reg.generic
  def foo(model):
      raise NotImplementedError

  thing = "Thing"

  r.register(foo, [Document], thing)

We've registered ``thing`` for generic ``foo`` of ``Document`` now,
not a function. Because ``thing`` is not a function, calling ``foo``
for ``Document`` will result in an error:

.. doctest::

  >>> foo(doc)
  Traceback (most recent call last):
    ...
  TypeError: 'str' object is not callable

We can still get at ``thing`` with a special method on the function called
``component``::

  >>> foo.component(doc)
  "thing"

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

  r.register(size, [HtmlDocument], htmldocument_size)

``size.all()`` for ``htmldoc`` now also gives back the more specific
``htmldocument_size``::

  >>> list(size.all(htmldoc))
  [<function htmldocument_size at ...>, <function document_size at ...>]

Using the Registry directly
---------------------------

The key under which we register something in a registry in fact doesn't
need to be a function. We can use any hashable object, such as a string:

.. testcode::

  r.register('some key', [Document], 'some registered')

We can't get it at it using a generic dispatch function anymore
now. We can use the :class:`reg.Lookup` API instead (in this case it's
provided by ``Registry`` directly). Here's what to do:

.. doctest::

  >>> r.component('some key', [doc])
  'some registered'
  >>> list(r.all('some key', [doc]))
  ['some registered']

Composition
===========

Reg separates the registration API from the lookup API. The
``Registry`` implementation we've been using combines both in one, but
we can separate the two instead. This is useful for a framework
developer that may want to allow the composition of multiple lookups
together. It also supports caching lookups to help performance.

ClassRegistry
-------------

:class:`reg.ClassRegistry` does not offer the full lookup API but does
still allows registration:

.. testcode::

  cr = reg.ClassRegistry()

We can use this to do registration as before:

.. testcode::

  @reg.generic
  def example():
      raise NotImplementedError

  def document_example(doc):
      return "Document Example"

  cr.register(example, [Document], document_example)

So far nothing is different. But ``ClassRegistry`` supports the *class
lookup* API that lets you lookup registrations by the *class* of
what was registered instead of by instance. Here's how:

.. doctest::

  >>> cr.get(example, [Document])
  <function document_example at ...>

It is still inheritance aware, too:

.. doctest::

  >>> cr.get(example, [HtmlDocument])
  <function document_example at ...>

We can get the original instance-based lookup API from a class lookup
by wrapping it in a ``Lookup``:

.. doctest::

  >>> l = reg.Lookup(cr)
  >>> l.component(example, [doc])
  <function document_example at ...>

Caching
-------

Now the fun starts. We can turn a class lookup in a faster, caching
class lookup using :class:`reg.CachingClassLookup`:

.. doctest::

  >>> caching = reg.CachingClassLookup(cr)
  >>> caching.get(example, [Document])
  <function document_example at ...>

Turning it back into a lookup gives us a caching version of what we had
before:

.. doctest::

  >>> caching_lookup = reg.Lookup(caching)
  >>> caching_lookup.component(example, [doc])
  <function document_example at ...>

You'll have to trust us on this, but it's faster the second time as
it's cached!

Composing class lookups
-----------------------

You can also compose class lookups together into a bigger class
lookup. This allows you to compose and partition behavior, sharing
behavior where you want it but isolating it otherwise.

The use case for this is a core framework that provides default
behavior, with applications written on top that extend or override
this default behavior. If one application overrides the behavior,
another application written on top of the same framework should not be
affected.

Let's look at an example of this. First we define three registries:
for the framework, for one application built with it, and for another
application built with it:

.. testcode::

  framework = reg.ClassRegistry()
  app = reg.ClassRegistry()
  other_app = reg.ClassRegistry()

We can now compose the ``framework`` and the ``app`` class lookup using
:class:`reg.ListClassLookup`:

.. testcode::

  app_combined = reg.Lookup(reg.ListClassLookup([app, framework]))

We compose the ``framework`` and the ``other_app`` class lookup
separately:

.. testcode::

  other_app_combined = reg.Lookup(reg.ListClassLookup([other_app, framework]))

Our hypothetical example framework provides a serialization API. The
idea is that we can call ``serialize`` on an object to get a
representation of that object as dictionaries and lists, JSON-style:

.. testcode::

  @reg.generic
  def serialize(obj):
     raise NotImplementedError

We've also provided a default serialization for documents in our
framework:

.. testcode::

  def document_serialize(doc):
     return { 'text': doc.text }

  framework.register(serialize, [Document], document_serialize)

Let's try it with the core framework itself:

.. doctest::

  >>> serialize(doc, lookup=reg.Lookup(framework))
  {'text': 'Hello world!'}

It also works in the ``app_combined`` application and the
``other_app_combined`` application:

.. doctest::

  >>> serialize(doc, lookup=app_combined)
  {'text': 'Hello world!'}
  >>> serialize(doc, lookup=other_app_combined)
  {'text': 'Hello world!'}

Now we decide that we want to override the default serialization for
``Document``, but only in ``app``, not in the framework itself, so
that ``other_app`` is unaffected:

.. testcode::

  def app_document_serialize(doc):
     return { 'content': 'The content: %s' % doc.text }

  app.register(serialize, [Document], app_document_serialize)

Our application has the new behavior now:

.. doctest::

  >>> serialize(doc, lookup=app_combined)
  {'content': 'The content: Hello world!'}

But our framework is not affected, and neither is ``other_app``:

.. doctest::

  >>> serialize(doc, lookup=reg.Lookup(framework))
  {'text': 'Hello world!'}
  >>> serialize(doc, lookup=other_app_combined)
  {'text': 'Hello world!'}

So far in this example we've used the explicit ``lookup``
argument. But how does this combine with the implict lookup facility?
Changing the implicit lookup before each application switch seems
daunting, but in practice you'd typically only switch the implicit
application context once per thread. The implicit lookup is thread
local, so that one thread's implicit lookup does not affect the other.
Multiple threads can this way run different applications all sharing
the same framework. This does require doing all the required
registrations during application startup time, and then not modifying
them anymore during run time, as registration is not thread-safe, just
lookup.
