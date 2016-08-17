Using Reg
=========

.. testsetup:: *

  pass

Introduction
------------

Reg implements *predicate dispatch* and *multiple registries*:

Predicate dispatch

  We all know about `dynamic dispatch`_: when you call a method on an
  instance it is dispatched to the implementation in its class, and
  the class is determined from the first argument (``self``).  This is
  known as *single dispatch*.

  Reg implements `multiple dispatch`_. This is a generalization of single
  dispatch: multiple dispatch allows you to dispatch on the class of
  *other* arguments besides the first one.

  Reg actually implements `predicate dispatch`_, which is a further
  generalization that allows dispatch on *arbitrary properties* of
  arguments, instead of just their class.

  The Morepath_ web framework is built with Reg. It uses Reg's
  predicate dispatch system. Its full power can be seen in its view
  lookup system.

  .. _`dynamic dispatch`: https://en.wikipedia.org/wiki/Dynamic_dispatch

  .. _`multiple dispatch`: http://en.wikipedia.org/wiki/Multiple_dispatch

  .. _`predicate dispatch`: https://en.wikipedia.org/wiki/Predicate_dispatch

Multiple registries

  Reg supports an advanced application architecture pattern where you
  have multiple predicate dispatch registries in the same
  runtime. This means that dispatch can behave differently depending
  on runtime context. You do this by using dispatch *methods* that you
  associate with a class that represents the application context. When
  you switch the context class, you switch the behavior.

  Morepath_ uses dispatch methods to support its application
  composition system, where one application can be mounted into
  another.

Reg is designed with a caching layer that allows it to support these
features efficiently.

.. _`Morepath`: http://morepath.readthedocs.io

Example
-------

Let's examine a short example. First we define a dispatch function
that dispatches based on the class of its ``obj`` argument:

.. testcode::

  import reg

  @reg.dispatch('obj')
  def title(obj):
     return "we don't know the title"

We want this function to return the title of its ``obj`` argument.

Now we create a few example classes for which we want to be able to use
the ``title`` fuction we defined above.

.. testcode::

  class TitledReport(object):
     def __init__(self, title):
        self.title = title

  class LabeledReport(object):
     def __init__(self, label):
        self.label = label

If we call ``title`` with a ``TitledReport`` instance, want it to return
its ``title`` attribute:

.. testcode::

  def titled_report_title(obj):
      return obj.title

If we call ``title`` with a ``LabeledReport`` instance, we want it to return
its ``label`` attribute:

.. testcode::

  def labeled_report_title(obj):
      return obj.label

We register these functions with the ``title`` dispatch function:

.. testcode::

  title.register(titled_report_title, obj=TitledReport)
  title.register(labeled_report_title, obj=LabeledReport)

Here we see that when ``obj`` is a ``TitledReport`` instance, we want
to use ``titled_report_title``, and when it's a ``LabeledReport``
instance, we want to use the ``labeled_report_title`` function.

Now generic ``title`` function works on both titled and labeled
objects:

.. doctest::

  >>> titled = TitledReport('This is a report')
  >>> labeled = LabeledReport('This is also a report')
  >>> title(titled)
  'This is a report'
  >>> title(labeled)
  'This is also a report'

What is going on and why is this useful at all? We present a worked
out example next.

Dispatch functions
==================

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

The ``Folder`` size code is generic; it doesn't care what the entries
inside it are; if they have a ``size`` method that gives the right
result, it will work. If a new content item ``Image`` is defined and
we provide a ``size`` method for this, a ``Folder`` instance that
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
  >>> folder.entries.append(image)
  >>> folder.size()
  25

Cool! So we're done, right?

Adding ``size`` from outside
----------------------------

.. sidebar:: Open/Closed Principle

  The `Open/Closed principle`_ states software entities should be open
  for extension, but closed for modification. The idea is that you may
  have a piece of software that you cannot or do not want to change,
  for instance because it's being developed by a third party, or
  because the feature you want to add is outside of the scope of that
  software (separation of concerns). By extending the software without
  modifying its source code, you can benefit from the stability of the
  core software and still add new functionality.

  .. _`Open/Closed principle`: https://en.wikipedia.org/wiki/Open/closed_principle

So far we didn't need Reg at all. But in a real world CMS we aren't
always in the position to change the content classes themselves. We
may be dealing with a content management system core where we *cannot*
control the implementation of ``Document`` and ``Folder``. Or perhaps
we can, but we want to keep our code modular, in independent
packages. So how would we add a size calculation feature in an
extension package?

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

There is a problem with the above function-based implementation
however: ``folder_size`` is not generic anymore, but now depends on
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

Now our generic ``size`` function works:

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
we want to switch behavior based on more than just one argument? Maybe
you even want different dispatch behavior depending on application
context? This is what Reg is for.

Doing this with Reg
-------------------

Let's see how we can implement ``size`` using Reg:

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

What this says that when we call ``size``, we want to dispatch based
on the class of its ``item`` argument.

We can now register the various size functions for the various content
items in a registry:

.. testcode::

  size.register(document_size, item=Document)
  size.register(folder_size, item=Folder)
  size.register(image_size, item=Image)
  size.register(file_size, item=File)

``size`` now works:

.. doctest::

  >>> size(doc)
  12

It works for folder too:

.. doctest::

  >>> size(folder)
  25

It works for subclasses too:

.. doctest::

  >>> size(htmldoc)
  19

Reg knows that ``HtmlDocument`` is a subclass of ``Document`` and will
find ``document_size`` automatically for you. We only have to register
something for ``HtmlDocument`` if we want to use a special, different
size function for ``HtmlDocument``.

Adapters
--------

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
      return path  # pretend we load the path here and return an image obj

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

But we want to be able to use the ``Icon`` API generically, so let's
create a generic function that gives us an implementation of ``Icon``
back for any object:

.. testcode::

  @reg.dispatch('obj')
  def icon(obj):
      raise NotImplementedError

We can now register the ``DocumentIcon`` adapter class for this
function and ``Document``:

.. testcode::

  icon.register(DocumentIcon, obj=Document)

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

  icon.register(ImageIcon, obj=Image)

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

Multiple and predicate dispatch
-------------------------------

Let's look at an example where dispatching on multiple arguments is
useful: a web view lookup system. Given a request object that
represents a HTTP request, and a model instance ( document, icon,
etc), we want to find a view function that knows how to make a
representation of the model given the request. Information in the
request can influence the representation. In this example we use a
``request_method`` attribute, which can be ``GET``, ``POST``, ``PUT``,
etc.

Let's first define a ``Request`` class with a ``request_method``
attribute:

.. testcode::

  class Request(object):
      def __init__(self, request_method, body=''):
          self.request_method = request_method
          self.body = body

We've also defined a ``body`` attribute which contains text in case
the request is a ``POST`` request.

We use the previously defined ``Document`` as the model class.

Now we define a view function that dispatches on the class of the
model instance, and the ``request_method`` attribute of the request:

.. testcode::

  @reg.dispatch(
    reg.match_instance('obj',
                       lambda obj: obj),
    reg.match_key('request_method',
                  lambda request: request.request_method))
  def view(obj, request):
      raise NotImplementedError

As you can see here we use ``match_instance`` and ``match_key``
instead of strings to specify how to dispatch.

If you use a string argument, this string names an argument and
dispatch is based on the class of the instance you pass in. Here we
use ``match_instance``, which is equivalent to this: we have a ``obj``
predicate which uses the class of the ``obj`` argument for dispatch.

We also use ``match_key``, which dispatches on the ``request_method``
attribute of the request; this attribute is a string, so dispatch is
on string matching, not ``isinstance`` as with ``match_instance``. You
can use any Python immutable with ``match_key``, not just strings.

We now define concrete views for ``Document`` and ``Image``:

.. testcode::

  def document_get(obj, request):
      return "Document text is: " + obj.text

  def document_post(obj, request):
      obj.text = request.body
      return "We changed the document"

Let's also define them for ``Image``:

.. testcode::

   def image_get(obj, request):
       return obj.bytes

   def image_post(obj, request):
       obj.bytes = request.body
       return "We changed the image"

We register the views:

.. testcode::

  view.register(document_get,
                request_method='GET',
                obj=Document)
  view.register(document_post,
                request_method='POST',
                obj=Document)
  view.register(image_get,
                request_method='GET',
                obj=Image)
  view.register(image_post,
                request_method='POST',
                obj=Image)

Let's try it out:

.. doctest::

  >>> view(doc, Request('GET'))
  'Document text is: Hello world!'
  >>> view(doc, Request('POST', 'New content'))
  'We changed the document'
  >>> doc.text
  'New content'
  >>> view(image, Request('GET'))
  'abc'
  >>> view(image, Request('POST', "new data"))
  'We changed the image'
  >>> image.bytes
  'new data'

Service Discovery
=================

Some applications need configurable services. The application may for
instance need a way to send email, but you don't want to hardcode any
particular way into your app, but instead leave this to a particular
deployment-specific configuration. You can use the Reg infrastructure
for this as well.

The simplest way to do this with Reg is by using a generic service lookup
function:

.. testcode::

  @reg.dispatch()
  def emailer():
      raise NotImplementedError

Here we've created a generic function that takes no arguments (and
thus does no dynamic dispatch). But you can still plug its actual
implementation into the registry from elsewhere:

.. testcode::

  sent = []

  def send_email(sender, subject, body):
      # some specific way to send email
      sent.append((sender, subject, body))

  def actual_emailer():
      return send_email

  emailer.register(actual_emailer)

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

  @reg.dispatch(reg.match_class('cls'))
  def something(cls):
      raise NotImplementedError()

Note the call to :func:`match_class` here. This lets us specify that
we want to dispatch on the class, in this case we simply want the
``cls`` argument.

Let's use it:

.. testcode::

  def something_for_object(cls):
      return "Something for %s" % cls

  something.register(something_for_object, cls=object)

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

  something.register(
      something_particular,
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

  size.register(htmldocument_size, item=HtmlDocument)

``size.all()`` for ``htmldoc`` now also gives back the more specific
``htmldocument_size``::

  >>> list(size.all(htmldoc))
  [<function htmldocument_size at ...>, <function document_size at ...>]

