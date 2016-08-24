Patterns
========

Here we look at a number of patterns you can implement with Reg.

Adapters
--------

What if we wanted to add a feature that required multiple methods, not
just one? You can use the adapter pattern for this.

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

We define ``Document`` and ``Image`` content classes:

.. testcode::

  class Document(object):
     def __init__(self, text):
         self.text = text

  class Image(object):
      def __init__(self, bytes):
          self.bytes = bytes

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

  >>> doc = Document("Hello world")
  >>> icon_api = DocumentIcon(doc)
  >>> icon_api.small()
  'document_small.png'
  >>> icon_api.large()
  'document_large.png'

But we want to be able to use the ``Icon`` API generically, so let's
create a generic function that gives us an implementation of ``Icon``
back for any object:

.. testcode::

  import reg

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
  >>> image = Image('abc')
  >>> icon(image).small()
  'image_small.png'
  >>> icon(image).large()
  'image_large.png'

Service Discovery
-----------------

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

Replacing class methods
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
