Using Reg
=========

.. testsetup:: *

  pass

Introduction
------------

Reg introduces a few clever registries that can help you build very
flexible pluggability systems for your Python project. See Reg as
infrastructure that helps you build more powerful registration APIs
for your applications and frameworks. Reg may seem like overkill to
you. You may very well be right; it depends on what you're building.

With Reg you can:

* look up a registered object that provides a certain interface/abc/class.

* do this lookup for zero or more objects.

* adapt an object to another with the desired interface/abc/class.

* look up a registered object according to other criteria (predicates).

Reg is very much aware of classes and inheritance. It provides an
approach to do `multiple dispatch`_ in Python.

.. _`multiple dispatch`: http://en.wikipedia.org/wiki/Multiple_dispatch

Interfaces
----------

An interface is simply a special kind of Python abc_ that you can also
use to look up objects that provide the interface of that abc. In
fact, Reg does not force you to use its own ``Interface``; you can do
everything using ``abc`` or even plain Python classes.

This is what an ``Interface`` looks like:

.. testcode::

  import reg

  class IEmailer(reg.Interface):
      @reg.abstractmethod
      def send(self, address, subject, body):
          "Send an email to address with subject and body."

.. sidebar:: ``I`` prefix

  The ``I`` prefix in ``IEmailer`` is just a convention to indicate
  that a class is an interface. It doesn't have any special meaning.

We can now subclass ``IEmailer`` to implement it:

.. testcode::

  class Emailer(IEmailer):
      def send(self, address, subject, body):
          pass # some implementation using the email module

When you instantiate ``Emailer``, you of course get something that is
an instance of ``IEmailer``:

.. doctest::

  >>> emailer = Emailer()
  >>> isinstance(emailer, IEmailer)
  True

That's all there is to it. It's identical to the way you'd use an
``abc``, and ``IEmailer`` is in fact an abc too.

.. _abc: http://docs.python.org/2/library/abc.html

Registration
------------

Imagine we have an application that needs to send email. We want to
make how it sends email configurable. The code that needs to send an
email looks up an ``IEmailer`` to send emailer, not caring about the
particular implementation. We can provide such an implementation using
a registry:

.. testcode::

  import reg
  r = reg.Registry()

We can now register our ``emailer`` as an ``IEmailer``:

.. testcode::

  r.register(IEmailer, [], emailer)

The first argument for register is the Interface (or class, or abc)
that we want to be able to look up. The second argument is a list of
those classes the object is registered for. In this case we don't
register it on any classes, so the list is empty. More about this
later. The third argument is the object (also called *component*, as
it provides an interface) we actually register, in this case our
``emailer``.

Lookup
------

Since ``reg.Registry`` is also has the lookup API, we can use it to look up
the ``IEmailer`` again:

.. doctest::

  >>> r.component(IEmailer, []) is emailer
  True

.. sidebar:: Separate registry and lookup

  While ``reg.Registry`` implements the ``IRegistry`` interface as
  well as the ``ILookup`` interface, Reg also allows you to use
  separate registry and lookup objects. This is useful when you want
  to combine lookup objects, and also helps with cacheability. More
  about this later.

Since what we look for is an interface, ``IEmailer``, we can also use
this alternate API:

.. doctest::

  >>> IEmailer.component(lookup=r) is emailer
  True

You can also install any lookup as an implicit global lookup. Here's how:

.. doctest::

  >>> from reg import implicit
  >>> implicit.initialize(r)

Once you have done that, you can write this, without the ``lookup`` argument:

.. doctest::

  >>> IEmailer.component() is emailer
  True

What have we gained?
--------------------

We could've just imported ``emailer`` and that would've been a lot
easier! That's true. What we've gained is the ability to register a
service for a library or application, in this case a service that can
send email. We have the ability to change what service is used without
having to change the code that uses that service. This is flexibility,
but at the cost of some indirection.

There are alternatives to accomplish this without using Reg, of
course. One way would be to simply provide a custom registration API,
along these lines::

  the_emailer = None

  def register_emailer(emailer):
     global the_emailer
     the_emailer = emailer

And then when you need the emailer, you can use ``the_emailer``.

That is totally reasonable and fine for many applications. Reg does a
lot more though. We'll go into this next.

Reg knows about inheritance
---------------------------

Let's look at an example involving inheritance. Let's define a
``ISignedEmailer`` interface that is a special kind of emailer:

.. testcode::

  class ISignedEmailer(IEmailer):
      pass

We'll imagine this is an emailer that adds a signature automatically
to each email sent. Let's create a class that implements the interface:

.. testcode::

  class SignedEmailer(ISignedEmailer):
      def send(self, address, subject, body):
          pass # some implementation here

We register an instance of this class as a ``ISignedEmailer``:

.. testcode::

  signed_emailer = SignedEmailer()
  r.register(ISignedEmailer, [], signed_emailer)

We can now look it up as an ``ISignedEmailer``:

.. doctest::

  >>> ISignedEmailer.component() is signed_emailer
  True

Since a ``ISignedEmailer`` is also an ``IEmailer`` because of
inheritance, we can also look for ``IEmailer`` and get the ``signed_emailer``
back:

.. doctest::

  >>> IEmailer.component() is emailer
  True

This works because Reg understands about inheritance.

A Hypothetical CMS
------------------

With Reg you can also register an object for another object. To
explain how that works, we will change our example. We're done with
emailers. We change the example to a hypothetical content management
system (CMS).

We'll start the CMS with two kinds of content item:

* a ``Document`` which contains some text.

* a ``Folder`` which contains a bunch of content items, for instance
  ``Document`` instances.

This is the implementation:

.. testcode::

  class Document(object):
     def __init__(self, text):
         self.text = text

  class Folder(object):
     def __init__(self, items):
         self.items = items

``size`` methods
----------------

Now we want to add a feature: we want the ability to calculate the
size (in bytes) of any content item. The size of the document is
defined as the length of its text (which for simplicity's sake we'll
fake being ``len(text)``), and the size of the folder is defined as
the sum of the size of everything in it.

If we have control over the implementation of ``Document`` and
``Folder`` can implement this easily by adding a ``size`` method to
both classes:

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

Let's see this work:

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

We'll note that the ``Folder`` size code is generic; it doesn't care
what the items inside it are, as long as they have a ``size`` method.

If a new content item ``Image`` is defined and we provide a ``size``
method for this, a ``Folder`` instance that contains ``Image``
instances will still be able to calculate its size. Let's try this:

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

So far we didn't need Reg at all. But in the real world things may be
a lot more complicated. We may be dealing with a content management
system core where we *cannot* control the implementation of
``Document`` and ``Folder``. What if we want to add a size calculation
feature in an extension package?

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

.. sidebar:: What about monkey patching?

  We *could* `monkey patch`_ a ``size`` method into all our content
  classes. This would work. It would however be dangerous - what if
  the original CMS's implementers change it so it *does* gain a size
  method or attribute, for instance? Multiple monkey patches
  interacting would also get difficult. The code also becomes harder
  to read: where is this ``size`` method coming from? It isn't there
  in the ``class`` statement! What about documentation?

  Monkey patching does not make for very maintainable code.

  .. _`monkey patch`: https://en.wikipedia.org/wiki/Monkey_patch

One way to accomplish this is by separating the size logic from the
classes altogether, and to use two functions instead:

.. testcode::

  def document_size(document):
      return len(document.text)

  def folder_size(folder):
      return sum([document_size(item) for item in folder.items])

Generic size
------------

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

We can write a ``generic_size`` function to get the size for any
item we give it:

.. testcode::

  def generic_size(item):
      if isinstance(item, Document):
          return document_size(item)
      elif isinstance(item, Image):
          return image_size(item)
      elif isinstance(item, Folder):
          return folder_size(item)
      assert False, "Unknown item: %s" % item

We can now rewrite ``folder_size`` to use ``generic_size``:

.. testcode::

  def folder_size(folder):
      return sum([generic_size(item) for item in folder.items])

Now our ``generic_size`` function will work::

.. doctest::

  >>> generic_size(doc)
  12
  >>> generic_size(image)
  3
  >>> generic_size(folder)
  25

A bit complicated, but it works!

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

What if we are actually yet another party, and we don't control the
basic CMS *nor* the size extension we presented above?

We cannot adjust ``generic_size`` to teach it about ``File`` now! Uh
oh!

Perhaps the implementers of the size extension were wise and anticipated
this use case. They could have implemented ``generic_size`` like this:

.. testcode::

  size_function_registry = {
     Document: document_size,
     Image: image_size,
     Folder: folder_size
  }

  def register_size(class_, function):
     size_function_registry[class_] = function

  def generic_size(item):
     return size_function_registry[item.__class__](item)

We can now use ``register_size`` to teach ``generic_size`` how to get
the size of a ``File`` instance:

.. testcode::

  register_size(File, file_size)

And it would work:

.. doctest::

  >>> generic_size(File('xyz'))
  3

To support this extensibility the writers of the size extension had to
be wise enough to create a registry and an API to extend and use it.

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
  >>> generic_size(htmldoc)
  Traceback (most recent call last):
     ...
  KeyError: ...

Uh oh, that doesn't work! There's nothing registered for the
``HtmlDocument`` class.

We need to remember to also call ``register_size`` for
``HtmlDocument``, even though ti's a subclass of ``Document`` and can
therefore use the ``document_size`` function already.

.. doctest::

  >>> register_size(HtmlDocument, document_size)

Now generic_size will work:

.. doctest::

  >>> generic_size(htmldoc)
  19

This is getting rather complicated, requiring not only quite a bit of
anticipation for the developers of ``generic_size`` but also extra
work for the person who wants to subclass a content item.

We could write a system that generalizes this and automates a lot of
this, making life easier. And that's Reg.

Doing this with Reg
-------------------

Let's see how we could implement ``generic_size`` using Reg.

First we need a special ``ISize`` interface that we can use to
register the various ``*_size`` functions under:

.. testcode::

  class ISize(reg.Interface):
      """Call me to get the size for the argument"""

Hey, we have something to hook documentation into as well here.

We can now register the various size functions for the various content
items:

.. testcode::

  r.register(ISize, [Document], document_size)
  r.register(ISize, [Folder], folder_size)
  r.register(ISize, [Image], image_size)
  r.register(ISize, [File], file_size)

Notice that we now finally use the second argument to ``register``, by
providing the class for which we want to register a size function.

Note also that the registry ``r`` is the same registry as the one
where we registered ``IEmailer`` earlier -- these registrations will
happily live side by side. We don't need to create a new registry for
each use case.

We can rewrite ``generic_size`` to make use of ``ISize``:

.. testcode::

  def generic_size(item):
      return ISize.component(item)(item)

This gets all the functionality we've hand-coded before::

.. doctest::

  >>> generic_size(doc)
  12
  >>> generic_size(folder)
  25

And also the ability to deal with new subclasses automatically:

.. doctest::

  >>> generic_size(htmldoc)
  19

Reg knows that ``HtmlDocument`` is a subclass of ``Document`` and will
find ``document_size`` automatically for you. We only have to register
something for ``HtmlDocument`` if we would want to use a special,
different size function for ``HtmlDocument``.

Much better!

Adaptation
----------

.. sidebar:: Use Reg directly or provide API?

  By using ``adapt()`` to implement ``generic_size``, this function
  became so simple we might as well advertise the use of
  ``ISize.adapt()`` directly to our users, and not implement a
  ``generic_size`` function at all.

  Doing so would expose the users of your API to Reg directly. The
  benefit of this is that they can now use the full power of Reg
  without you doing more than declare an Interface and registering
  things for it. The drawback is that the users of your API will have
  to learn about Reg in order to use it. It's up to you.

  The same tradeoffs apply to the registration functionality; do you
  write custom ``register_`` functions in your API and hide Reg, or do
  you expose a Reg registry directly? Again, it's up to you.

In our new ``generic_size`` we do two things:

* look up the ``ISize`` function for the item.

* immediately call that function with the item again.

It turns out this is a very common pattern, and we a special name for
it: *adaptation*. We adapt a content item to its size, so to speak.

Reg offers a shortcut for adaptation: ``adapt()``. We can rewrite
``generic_size`` to use the ``.adapt`` call instead:

.. testcode::

  def generic_size(item):
     return ISize.adapt(item)

.. doctest::

  >>> generic_size(doc)
  12

``adapt()`` will look up the registered component for its arguments,
and then immediately *call* that object again with these arguments.

Using classes as adapters
-------------------------

The above example worked well for a single function to get the size,
but what if we wanted to add a feature that required multiple methods,
not just one?

Let's imagine we have a feature to get the icon for a content object
in our CMS, and that this consists of two methods, with a way to get a
small icon and a large icon:

.. testcode::

  class IIcon(reg.Interface):
      @reg.abstractmethod
      def small(self):
          pass
      @reg.abstractmethod
      def large(self):
          pass

An implementation of this for ``Document`` might look like this:

.. testcode::

  def load_icon(path):
      return path # pretend we load the path here and return an image obj

  class DocumentIcon(IIcon):
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
``large`` methods use this instance to determine what icon to produce.

We call ``DocumentIcon`` an adapter, and we can use it manually:

.. doctest::

  >>> icon_api = DocumentIcon(doc)
  >>> icon_api.small()
  'document_small.png'
  >>> icon_api.large()
  'document_large.png'

We register the ``DocumentIcon`` adapter class instead of a function:

.. testcode::

  r.register(IIcon, [Document], DocumentIcon)

We can also register a ``FolderIcon`` adapter for ``Folder``, a
``ImageIcon`` adapter for ``Image``, and so on. For the sake of
brevity let's only define one for ``Image`` here:

.. testcode::

  class ImageIcon(IIcon):
      def __init__(self, image):
          self.image = image

      def small(self):
          return load_icon('image_small.png')

      def large(self):
          return load_icon('image_large.png')

  r.register(IIcon, [Image], ImageIcon)

Now we can use the ``IIcon`` interface to retrieve the API defined by
``IIcon`` for any item in the system for which an adapter is
registered::

.. doctest::

  >>> icon_api = IIcon.adapt(doc)
  >>> icon_api.small()
  'document_small.png'
  >>> icon_api.large()
  'document_large.png'
  >>> IIcon.adapt(image).small()
  'image_small.png'
  >>> IIcon.adapt(image).large()
  'image_large.png'

