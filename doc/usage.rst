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

  This document explains how to use Reg. Various specific patterns are
  documented in :doc:`patterns`.

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

  Morepath_ uses context-based dispatch to support its application
  composition system, where one application can be mounted into
  another.

  See :doc:`context` for this advanced application pattern.

Reg is designed with a caching layer that allows it to support these
features efficiently.

.. _`Morepath`: http://morepath.readthedocs.io

Example
-------

Let's examine a short example. First we use the :meth:`reg.dispatch`
decorator to define a function that dispatches based on the
class of its ``obj`` argument:

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

If we call ``title`` with a ``TitledReport`` instance, we want it to return
its ``title`` attribute:

.. testcode::

  @title.register(obj=TitledReport)
  def titled_report_title(obj):
      return obj.title

The ``title.register`` decorator registers the function
``titled_report_title`` as an implementation of ``title`` when ``obj``
is an instance of ``TitleReport``.

There is also a more programmatic way to register implementations.
Take for example, the implementation of ``title`` with a ``LabeledReport``
instance, where we want it to return its ``label`` attribute:

.. testcode::

  def labeled_report_title(obj):
      return obj.label

We can register it by explicitely invoking ``title.register``:

.. testcode::

  title.register(labeled_report_title, obj=LabeledReport)

Now the generic ``title`` function works on both titled and labeled
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
------------------

A Hypothetical CMS
~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~

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
items as implementations of ``size``:

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
    reg.match_instance('obj'),
    reg.match_key('request_method',
                  lambda obj, request: request.request_method))
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

  @view.register(request_method='GET', obj=Document)
  def document_get(obj, request):
      return "Document text is: " + obj.text

  @view.register(request_method='POST', obj=Document)
  def document_post(obj, request):
      obj.text = request.body
      return "We changed the document"

Let's also define them for ``Image``:

.. testcode::

  @view.register(request_method='GET', obj=Image)
  def image_get(obj, request):
      return obj.bytes

  @view.register(request_method='POST', obj=Image)
  def image_post(obj, request):
      obj.bytes = request.body
      return "We changed the image"

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

Dispatch methods
----------------

Rather than having a ``size`` function and a ``view`` function, we can
also have a context class with ``size`` and ``view`` as methods. We
need to use :class:`reg.dispatch_method` instead of
:class:`reg.dispatch` to do this.

.. testcode::

  class CMS(object):

      @reg.dispatch_method('item')
      def size(self, item):
          raise NotImplementedError

      @reg.dispatch_method(
          reg.match_instance('obj'),
          reg.match_key('request_method',
                        lambda self, obj, request: request.request_method))
      def view(self, obj, request):
          return "Generic content of {} bytes.".format(self.size(obj))

We can now register an implementation of ``CMS.size`` for a
``Document`` object:

.. testcode::

  @CMS.size.register(item=Document)
  def document_size_as_method(self, item):
      return len(item.text)

Note that this is almost the same as the function ``document_size`` we
defined before: the only difference is the signature, with the
additional ``self`` as the first argument. We can in fact use
:func:`reg.methodify` to reuse such functions without an initial
context argument:

.. testcode::

  from reg import methodify

  CMS.size.register(methodify(folder_size), item=Folder)
  CMS.size.register(methodify(image_size), item=Image)
  CMS.size.register(methodify(file_size), item=File)

``CMS.size`` now behaves as expected:

.. doctest::

  >>> cms = CMS()
  >>> cms.size(Image("123"))
  3
  >>> cms.size(Document("12345"))
  5

Similarly for the ``view`` method we can define:

.. testcode::

  @CMS.view.register(request_method='GET', obj=Document)
  def document_get(self, obj, request):
      return "{}-byte-long text is: {}".format(
          self.size(obj), obj.text)

This works as expected as well:

.. doctest::

  >>> cms.view(Document("12345"), Request("GET"))
  '5-byte-long text is: 12345'
  >>> cms.view(Image("123"), Request("GET"))
  'Generic content of 3 bytes.'

For more about how you can use dispatch methods and class-based context,
see :doc:`context`.

Lower level API
---------------

Component lookup
~~~~~~~~~~~~~~~~

You can look up the function that a function would dispatch to without
calling it. You do this using the :meth:`reg.Dispatch.component`
method on the dispatch function:

.. doctest::

  >>> size.component(doc) is document_size
  True

Sometimes it's useful to have more control and go to a lower level by
specifying the keys that go in directly. We can use
:meth:`reg.Dispatch.component_by_keys` for that:

  >>> size.component_by_keys(item=Document) is document_size
  True

Getting all
~~~~~~~~~~~

As we've seen, Reg supports inheritance. ``size`` for instance was
registered for ``Document`` instances, and is therefore also available
of instances of its subclass, ``HtmlDocument``:

.. doctest::

  >>> size.component(doc) is document_size
  True
  >>> size.component(htmldoc) is document_size
  True

Using the special :meth:`reg.Dispatch.all` method we can also get an
iterable of *all* the components registered for a particular instance,
including those of base classes. Right now this is pretty boring as
there's only one of them:

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

Predicate key
~~~~~~~~~~~~~

In some cases it can be useful to get an immutable key that represents
a dispatch registration. The Morepath web framework uses this for
instance to determine whether registrations are identical in its
conflict detection and override system.

Earlier we registered various views for object and request method. We
can get immutable keys for such registrations using
:meth:`reg.Dispatch.key_dict_to_predicate_key`:

.. doctest::

   >>> view.key_dict_to_predicate_key(
   ...  {'request_method': 'GET', 'obj': Document})
   (<class 'Document'>, 'GET')
   >>> view.key_dict_to_predicate_key(
   ...  {'obj': Image, 'request_method': 'POST'})
   (<class 'Image'>, 'POST')
