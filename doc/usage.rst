Using Reg
=========

.. testsetup:: *

  pass

Introduction
------------

Reg implements *predicate dispatch* and *pluggable registries*:

Predicate dispatch

  We all know about `dynamic dispatch`_: a method call is dispatched
  on its first argument: ``self``, typically based on its class. This
  is known as single dispatch. Reg implements `multiple dispatch`_,
  which generalizes this by allowing dispatch on the class of *other*
  arguments as well. Reg actually implements `predicate dispatch`_,
  which is a further generalization that allows dispatch on arbitrary
  properties of arguments, instead of just the class.

  The Morepath_ web framework uses the full power of predicate
  dispatch in its view lookup system.

  .. _`dynamic dispatch`: https://en.wikipedia.org/wiki/Dynamic_dispatch

  .. _`multiple dispatch`: http://en.wikipedia.org/wiki/Multiple_dispatch

  .. _`predicate dispatch`: https://en.wikipedia.org/wiki/Predicate_dispatch

Pluggable registries

  Reg lets you have multiple predicate dispatch registries in the same
  runtime: each can dispatch differently.

  Morepath_ uses multiple pluggable registries to support its
  application composition system (mounting).

To support these features efficiently, Reg also makes heavy use of
caching throughout.

.. _`Morepath`: http://morepath.readthedocs.io

Example
-------

Let's look at an example. First we create a class that when
instantiated has a ``lookup`` attribute. This ``lookup`` attribute is
used by Reg to look up the function to which it dispatches. We also define
a single method it marked with the ``dispatch_method`` decorator:

.. testcode::

  import reg

  class Example(object):
      def __init__(self, lookup):
          self.lookup = lookup

      @reg.dispatch_method('obj')
      def title(self, obj):
          return "We don't know the title"

Now we create a few classes for which we want to be able to use the
``title`` method we defined above:

.. testcode::

  class TitledReport(object):
      def __init__(self, title):
          self.title = title

  class LabeledReport(object):
      def __init__(self, label):
          self.label = label

In ``TitledReport`` there's an attribute called ``title`` but in the
``LabeledReport`` case we have an attribute ``label`` we want to use
as the title. We implement this behavior in a few plain python
functions:

.. testcode::

  def titled_report_title(self, obj):
      return obj.title

  def labeled_report_title(self, obj):
      return obj.label

We can now create a registry that knows that we want to use
``titled_report_title`` with instances of ``TitledReport`` and
``labeled_report_title`` with instances of ``LabeledReport``:

.. testcode::

  r = reg.Registry()
  r.register_method(
      Example.title, titled_report_title, obj=TitledReport)
  r.register_method(
      Example.title, labeled_report_title, obj=LabeledReport)

We can now create a ``lookup`` object for this registry. The lookup is
an object that uses a registry to find and call the correct registered
implementations:

.. testcode::

  lookup = r.lookup()

We can now instantiate ``Example`` with this lookup:

.. testcode::

  example = Example(lookup)

Once we've done this, we can use ``example.title`` with both titled
and labeled objects:

.. doctest::

  >>> titled = TitledReport('This is a report')
  >>> labeled = LabeledReport('This is also a report')
  >>> example.title(titled)
  'This is a report'
  >>> example.title(labeled)
  'This is also a report'

What is going on and why is this useful at all? We present a worked
out example next.

Dispatch methods
================

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
  unicode. Just pretend that text is in ASCII for the sake of this
  example.

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
``Document`` and ``Folder``. Or perhaps we can, but we want to keep
our code modular anyway. So how would we add a size calculation
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
``document_size``. It fails when presented with a folder with an
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

What if we want to write a new extension to our CMS that adds a new
kind of folder item, the ``File``, with a ``file_size`` function?

.. testcode::

  class File(object):
     def __init__(self, bytes):
         self.bytes = bytes

  def file_size(item):
      return len(item.bytes)

We need to remember to adjust the generic ``size`` function so we can
teach it about ``file_size`` as well. Annoying, tightly coupled, but
sometimes doable.

But what if we are actually another party, and we have control of
neither the basic CMS *nor* its size extension? We cannot adjust
``generic_size`` to teach it about ``File`` now! Uh oh!

Perhaps the implementers of the size extension anticipated this use
case. They could have implemented ``size`` like this:

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

And it works:

.. doctest::

  >>> size(File('xyz'))
  3

But this is quite a bit of custom work that the implementers need to
do, and it involves a new API (``register_size``) to manipulate the
``size_function_registry``.  But it can be done.

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

That doesn't work! There's nothing registered for the ``HtmlDocument``
class.

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

Hey, we should write a system that automates a lot of this, and gives
us a universal registration API, making our life easier! And what if
we want to switch behavior based on more than just one argument? Plus
we might want more than one registry in the same application. That's
what Reg does.

Doing this with Reg
-------------------

Let's see how we can implement ``size`` using Reg:

.. sidebar:: Why is size a method?

  Reg (as of version 0.10) requires you implement ``size`` as a
  *method*, but not a method on the content objects. Reg requires this
  because it supports multiple registries in the same application, and
  the instance that the method is attached to determines which
  registry is in use.

  This way we can make what registry is used for lookup explicit: the
  lookup is determined by looking at the first (``self`` or ``cls``)
  argument of the method (or ``classmethod``).

.. testcode::

  class App(object):
      def __init__(self, lookup):
          self.lookup = lookup

      @reg.dispatch_method('item')
      def size(self, item):
          raise NotImplementedError

This method raises ``NotImplementedError`` as we don't know how to get
the size for an arbitrary Python object. Not very useful yet. We need
to be able to hook the actual implementations into it. That's why the
``@reg.dispatch_method`` decorator is here. To be able to use any
dispatch method the instance must have a ``lookup`` attribute, so we
set this up when we initialize ``App``.

We can now register the various size functions for the various content
items in a registry:

.. testcode::

  r = reg.Registry()
  r.register_function(App.size, document_size, item=Document)
  r.register_function(App.size, folder_size, item=Folder)
  r.register_function(App.size, image_size, item=Image)
  r.register_function(App.size, file_size, item=File)

Note that we've used ``register_function`` here instead of
``register_method``. We can use ``register_function`` when we want to
register plain functions which don't define a ``self`` or ``cls``
first argument.

Now we need to create an ``App`` instance with a lookup based on the registry:

.. testcode::

   app = App(r.lookup())

We can now use our ``size`` method:

.. doctest::

  >>> app.size(doc)
  12

And it will work for folder too:

.. doctest::

  >>> app.size(folder)
  25

It will work for subclasses too:

.. doctest::

  >>> app.size(htmldoc)
  19

Reg knows that ``HtmlDocument`` is a subclass of ``Document`` and will
find ``document_size`` automatically for you. We only have to register
something for ``HtmlDocument`` if we would want to use a special,
different size function for ``HtmlDocument``.

Using classes
-------------

The previous example worked well for a single method to get the size,
but what if we wanted to add a feature that required multiple methods,
not just one?

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

But we want to be able to use the ``Icon`` API in a generic way, so
let's create a dispatch method that gives us an implementation of
``Icon`` back for any object:

.. testcode::

  class App(object):
       def __init__(self, lookup):
           self.lookup = lookup

       @reg.dispatch_method('obj')
       def icon(self, obj):
           raise NotImplementedError

We register the ``DocumentIcon`` adapter class for this method and
``Document``:

.. testcode::

  r.register_function(App.icon, DocumentIcon, obj=Document)

Let's set up an ``App`` instance with the correct lookup:

.. testcode::

  app = App(r.lookup())

We can use the dispatch method ``icon`` to get ``Icon`` API for a
document now:

.. doctest::

  >>> api = app.icon(doc)
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

  r.register_function(App.icon, ImageIcon, obj=Image)

Now we can use ``icon`` to retrieve the ``Icon`` API for any item in
the system for which an adapter was registered:

.. doctest::

  >>> app.icon(doc).small()
  'document_small.png'
  >>> app.icon(doc).large()
  'document_large.png'
  >>> app.icon(image).small()
  'image_small.png'
  >>> app.icon(image).large()
  'image_large.png'

Multiple and predicate dispatch
-------------------------------

Sometimes we want to dispatch on multiple arguments. A good example
for this is a web view lookup system. Given a request and a model, we
want to find a view that knows how to make a representation of the
model given the request. Information in the request can influence the
representation. In this example we use the ``request_method``. This
can can be ``GET``, ``POST``, ``PUT``, etc. The request method used
determines to which actual view function Reg dispatches.

Let's imagine we have a ``Request`` class with a ``request_method``
attribute:

.. testcode::

  class Request(object):
      def __init__(self, request_method):
          self.request_method = request_method

We use ``Document`` as the model class.

Now we define a view function that dispatches on the class of the
model instance, and the ``request_method`` attribute of the request:

.. testcode::

  class App(object):
      def __init__(self, lookup):
          self.lookup = lookup

      @reg.dispatch_method(
          reg.match_instance('model',
                             lambda model: model),
          reg.match_key('request_method',
                        lambda request: request.request_method))
      def view(self, model, request):
          raise NotImplementedError

As you can see here we use ``match_instance`` and ``match_key``
instead of strings to specify how to dispatch. If you use a string
argument, this string names an argument and dispatch is based on its
class. Here we use ``match_instance``, which is equivalent to this: we
have a ``model`` predicate which uses the class of the ``model``
argument for dispatch. We also use ``match_key``, which dispatches on
the ``request_method`` attribute of the request; this attribute is a
string, so dispatch is on string matching, not ``isinstance`` as with
``match_instance``.

We now define a concrete view for ``Document``:

.. testcode::

  def document_get(self, model, request):
      return "GET for document is: " + model.text

  def document_post(self, model, request):
      return "POST for document"

We register the view in the registry:

.. testcode::

  r.register_method(App.view, document_get,
                    request_method='GET', model=Document)
  r.register_method(App.view, document_post,
                    request_method='POST', model=Document)

For ``model`` we've specified the class that matches (``Document``),
but for the ``request_method`` predicate we've given the key to match
on, the strings ``"GET"`` and ``"POST"``.

We create the app instance:

.. testcode::

  app = App(r.lookup())

We can now call ``app.view``:

.. doctest::

  >>> app.view(doc, Request('GET'))
  'GET for document is: Hello world!'
  >>> app.view(doc, Request('POST'))
  'POST for document'

Service Discovery
=================

Sometimes you want your application to have configurable services. The
application may for instance need a way to send email, but you don't
want to hardcode any particular way into your app, but instead leave
this to a particular deployment-specific configuration. You can use the Reg
infrastructure for this as well.

The simplest way to do this with Reg is by using a method that finds
the service for your application:

.. testcode::

  class App(object):
      def __init__(self, lookup):
          self.lookup = lookup

      @reg.dispatch_method()
      def emailer(self):
          raise NotImplementedError

Here we've created a generic method that takes no arguments (besides
self) and thus no dynamic dispatch. But it still makes use of the
lookup, so we can plug in its actual implementation elsewhere:

.. testcode::

  sent = []

  def send_email(sender, subject, body):
      # some specific way to send email
      sent.append((sender, subject, body))

  def actual_emailer(self):
      return send_email

  r.register_method(App.emailer, actual_emailer)

We instantiate with a ``lookup`` again:

.. testcode::

  app = App(r.lookup())

When we call ``App.emailer``, we get the specific service we want:

.. doctest::

  >>> the_emailer = app.emailer()
  >>> the_emailer('someone@example.com', 'Hello', 'hello world!')
  >>> sent
  [('someone@example.com', 'Hello', 'hello world!')]

In this case what we expect from the service is a function that we can
call to send email. But you can register a function that returns a
more complex object as a service just as easily.

replacing class methods
-----------------------

Reg's dispatch system can be used to replace methods, as you can
dispatch on the class of an argument. This way you can follow the
open/closed principle and add functionality to a class without
modifying it. They can also be used to replace classmethods marked
with ``classmethod``. This takes the *class* as the first argument,
not an instance.

Here's what it looks like:

.. testcode::

  class App(object):
      def __init__(self, lookup):
          self.lookup = lookup

      @reg.dispatch_method(
         reg.match_class('cls', lambda cls: cls))
      def something(self, cls):
         raise NotImplementedError()

Note the call to :func:`match_class` here. This lets us specify that
we want to dispatch on the class, and we supply a lambda function that
shows how to extract this from the arguments to ``something``; in this
case we simply want the ``cls`` argument.

Let's use it:

.. testcode::

  def something_for_object(self, cls):
      return "Something for %s" % cls

  class DemoClass(object):
      pass

  r.register_method(App.something, something_for_object, cls=DemoClass)

  app = App(r.lookup())

When we now call ``something()`` with ``DemoClass`` as the first
argument we get the expected output:

.. doctest::

  >>> app.something(DemoClass)
  "Something for <class 'DemoClass'>"

This also knows about inheritance. Here's a subclass of ``DemoClass``:

.. testcode::

  class ParticularClass(DemoClass):
      pass

.. doctest::

   >>> app.something(ParticularClass)
   "Something for <class 'ParticularClass'>"

We can also register something more specific for ``ParticularClass``:

.. testcode::

  def something_particular(self, cls):
      return "Particular for %s" % cls

  r.register_method(App.something, something_particular,
                    cls=ParticularClass)

When we call ``something`` now with ``ParticularClass`` as the argument,
then ``something_particular`` is called:

.. doctest::

  >>> app.something(ParticularClass)
  "Particular for <class 'ParticularClass'>"

Lower level API
===============

Component lookup
----------------

You can look up the function that a method would dispatch to without
calling it. You do this using the ``component`` method on the dispatch
function:

.. testcode::

  class App(object):
      def __init__(self, lookup):
          self.lookup = lookup

      @reg.dispatch_method('obj')
      def foo(self, obj):
          return "default"

  class A(object):
      pass

  def a_func(self, obj):
      return "A"

  r = reg.Registry()
  r.register_method(App.foo, a_func, obj=A)

  app = App(r.lookup())

  a = A()

.. doctest::

  >>> app.foo(a)
  'A'
  >>> app.foo.component(a) is a_func
  True

Getting all
-----------

As we've seen, Reg supports inheritance. ``foo`` had a registration for
``A`` so it also applies to ``B`` if it subclasses ``A``:

.. testcode::

  class B(A):
      pass

  b = B()

.. doctest::

  >>> app.foo(a)
  'A'
  >>> app.foo(b)
  'A'
  >>> app.foo.component(a) is a_func
  True
  >>> app.foo.component(b) is a_func
  True

Using the special ``all`` function we can also get an iterable of
*all* the components registered for a particular instance, including
those of base classes. Right now this is pretty boring as there's
only one of them:

.. doctest::

  >>> list(app.foo.all(a)) == [a_func]
  True
  >>> list(app.foo.all(b)) == [a_func]
  True

Let's create another subclass of ``A``:

.. testcode::

   class C(A):
       pass

   c = C()

We now register a special ``c_func`` for it:

.. testcode::

  def c_func(self, obj):
      return "C"

  r.register_method(App.foo, c_func, obj=C)

When we use ``all`` now, we get back the ``c_func`` specifically registered
for it, and also ``a_func`` which is registered for its base class ``A``:

.. doctest::

  >>> list(app.foo.all(c)) == [c_func, a_func]
  True

Using the Registry directly
---------------------------

Until now we've seen access through the high-level API of Reg,
centered around calling methods. We can also use the registry API
directly. In this case we aren't registered to registering functions
for methods; we can register anything for any immutable key:

.. testcode::

  lowlevel_r = reg.Registry()

  lowlevel_r.register_predicates('some key', [reg.match_argname('obj')])

We can now register something for this key:

.. testcode::

  lowlevel_r.register_value('some key', [Document], 'some registered')

We can access the information in the registry using the :class:`reg.Registry`
API:

.. doctest::

  >>> lowlevel_r.component('some key', Document)
  'some registered'
  >>> list(lowlevel_r.all('some key', Document))
  ['some registered']

Caching
-------

The default lookup that we get from a registry is designed to be easy
to understand and debug, but it is relatively slow. In real-world
applications it is useful to introduce caching. We can use
:class:`reg.CachingKeyLookup` for this:

.. testcode::

  caching = reg.CachingKeyLookup(r, 100, 100, 100)

This isn't a lookup yet: it's a *key lookup*, which is a lower layer
in the API. We can turn it back into a lookup to give us a caching
version:

.. testcode::

   caching_lookup = caching.lookup()

We can now create a caching application:

.. testcode::

  caching_app = App(caching_lookup)

It behaves the same way as the original:

.. doctest::

  >>> caching_app.foo(a)
  'A'
  >>> caching_app.foo(b)
  'A'
  >>> caching_app.foo(c)
  'C'

But if you call the dispatch method again with the same arguments, the
second time the dispatch is faster because it can skip looking through
indexes.
