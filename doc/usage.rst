Using Reg
=========

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

This is what an ``Interface`` looks like::

  import reg

  class IEmailer(reg.Interface):
      @reg.abstractmethod
      def send(self, address, subject, body):
          "Send an email to address with subject and body."

The ``I`` prefix in ``IEmailer`` is just a convention to indicate that
a class is an interface.

We can now subclass ``IEmailer`` to implement it::

  class Emailer(IEmailer):
    def sender(self, address, subject, body):
      # some implementation using the email module

When you instantiate ``Emailer``, you of course get something that is
an instance of ``IEmailer``::

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
a registry::

  import reg
  r = reg.Registry()

We can now register our ``emailer`` as an ``IEmailer``::

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
the ``IEmailer`` again::

  >>> r.component(IEmailer, []) is emailer
  True

Since what we look for is an interface, ``IEmailer``, we can also use
this alternate API::

  >>> IEmailer.component(lookup=r) is emailer
  True

You can also install any lookup as an implicit global lookup. Here's how::

  >>> from reg import implicit
  >>> implicit.lookup = r

Once you have done that, you can write this::

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
lot more though, especially in more advanced situations. We'll go into
this next.

Reg knows about inheritance
---------------------------

Let's look at an example involving inheritance. Let's define a
``ISignedEmailer`` interface that is a special kind of emailer::

  class ISignedEmailer(IEmailer):
      pass

We'll imagine this is an emailer that adds a signature automatically
to each email sent. Let's create a class that implements the interface::

  class SignedEmailer(ISignedEmailer):
      ...

And let's register an instance of this class as a ``ISignedEmailer``::

  >>> signed_emailer = SignedEmailer()
  >>> r.register(ISignedEmailer, [], signed_emailer)

We can look it up as an ``ISignedEmailer``::

  >>> ISignedEmailer.component(lookup=r) is signed_emailer
  True

But since a ``ISignedEmailer`` is also an ``IEmailer`` because of inheritance,
we'll also get the ``signed_emailer`` object if we look for an ``IEmailer``::

  >>> IEmailer.component(lookup=r) is emailer

This works because Reg understands about inheritance.

A Hypothetical CMS
------------------

With Reg you can also register an object for another object. Let's
change the examplew to a hypothetical content management system (CMS)
to learn more about how this might work. Our CMS has two kinds of
object, a ``Document`` which contains some text, and a ``Folder``
which contains a bunch of content items, for instance ``Document``
instances::

  class Document(object):
     def __init__(self, text):
         self.text = text

  class Folder(object):
     def __init__(self, items):
         self.items = items

``size`` methods
----------------

Now let's say we want to add a feature: we want the ability to
calculate the size (in characters) of any object, so for ``Document``
and ``Folder``. We define the size of the folder as the sum of the
size of everything in it.

If we have control over the implementation of ``Document`` and
``Folder`` can implement this by adding a ``size`` method to both
classes::

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

We'll note that the ``Folder`` size code is generic. If a new content
item ``Image`` is defined and we provide a ``size`` method for this, a
``Folder`` instance that contains ``Image`` instances will still be
able to calculate its size.

Adding ``size`` from outside
----------------------------

Now what if we *don't* have control over the implementation of
``Document`` and ``Folder``, and we want to add a size calculation feature
from an extension of the core application? (see `Open/Closed principle`_ for
more on this topic).

.. _`Open/Closed principle`: https://en.wikipedia.org/wiki/Open/closed_principle

We can do this by separating out the logic into two functions::

  def document_size(document):
      return len(document.text)

  def folder_size(folder):
      return len([document_size(item) for item in folder.items])

Generic size
------------

There is a problem however: ``folder_size`` will fail if the folder
contains something else than a document, for instance ``Image``. We've
lost the generic nature of ``size()`` on ``Folder``. We can bring it back::

  def generic_size(item):
      if isinstance(item, Document):
          return document_size(item)
      elif isinstance(item, Image):
          return image_size(item)
      elif isinstance(item, Folder):
          return folder_size(item)
      assert False, "Unknown item: %s" % item

We can then adjust ``folder_size`` to use ``generic_size`` in its
implementation::

  def folder_size(folder):
      return len([generic_size(item) for item in folder.items])

New ``File`` content
--------------------

But what if we now want to write a new extension to our CMS that adds
a new kind of folder item, the ``File``, with a ``file_size``
function?

We'd need to adjust ``generic_size`` to know about ``File`` as well,
but ``generic_size`` already lives in another extension that
deals with sizes, and knows nothing about this new ``File`` item. To
resolve this, our next move could be to provide a registry in our size
extension::

  size_function_registry = {
     Document: document_size,
     Image: image_size,
     Folder: folder_size
  }

  def generic_size(item):
     return size_function_registry[item.__class__](item)

We can now put in ``file_size`` in this registry to teach ``generic_size``
how to get the size of a ``File`` instance::

  >>> size_function_registry[File] = file_size

New ``HtmlDocument`` content
----------------------------

But what if we introduce a new ``HtmlDocument`` item that is a subclass of
``Document``? We need to remember to let the size_function_registry know
that it can *still* use ``document_size`` to calculate its size::

  >>> size_function_registry[HtmlDocument] = document_size

All this is starting to get quite complicated. Reg can help.

Doing this with Reg
-------------------

First we need a special ``ISize`` interface that we can use to
register the various ``*_size`` functions under::

  class ISize(reg.Interface):
      """Call me to get the size for the argument"""

Now that we have this, we can register the various size functions for
the various content items::

  r.register(ISize, [Document], document_size)
  r.register(ISize, [Folder], folder_size)

Notice that we now finally use the second argument to ``register``, by
providing the class for which we want to register a size function.

Note that the registry ``r`` could be the same registry as the one
where we registered ``IEmailer`` earlier -- these registrations will
happily live side by size. We don't need to create a new registry for
each use case.

We can now rewrite ``generic_size`` to make use of this registry::

  def generic_size(item):
     return ISize.component(item, lookup=r)(item)

Whenever a new content item is defined, we register its size
function.

We don't need to do it for subclasses however, so this registration
for ``HtmlDocument`` would be superfluous as we already have one for
``Document``::

  r.register(ISize, [HtmlDocument], document_size)

Reg knows that ``HtmlDocument`` is a subclass of ``Document`` and will
find ``document_size`` anyway. We only have to register something for
``HtmlDocument`` if we would want to use a special, different size
function for ``HtmlDocument``.

Much better!

Adaptation
----------

Above in ``generic_size`` we looked up the ``ISize`` function for the
item, and then immediately call that function with the item again. We
see this pattern a lot, and call this *adaptation*. We adapt a content
item to its size, so to speak.

Reg offers a shortcut for adaptation: ``adapt()``. We can rewrite
``generic_size`` to use the ``.adapt`` call instead::

  def generic_size(item):
     return ISize.adapt(item, lookup=r)

``adapt()`` will look up the registered component for its arguments,
and then immediately *call* that object again with these arguments.

Using classes as adapters
-------------------------

The above example worked well for a single function to get the size,
but what if we wanted to add a feature that required multiple methods,
not just one? Let's imagine we have a feature to get the icon for a
content object in our CMS, and that this consists of two methods, a
way to get a small icon and a large icon::

  class IIcon(reg.Interface):
      @reg.abstractmethod
      def small(self):
          pass
      @reg.abstractmethod
      def large(self):
          pass

An implementation of this for ``Document`` might look like this::

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

Note that the constructor of ``DocumentIcon`` receives a ``Document``
instance as its first argument, and that the implementation of the
``small`` and ``large`` methods use this instance to determine what
icon to produce.

We can register this in the familiar way, but here we register the
``DocumentIcon`` class instead of a function::

  r.register(IIcon, [Document], DocumentIcon)

Now whenever we want the ``IIcon`` API (or *adapter*) for an item, we
adapt that item to it, and then call methods on the API::

  icon_api = IIcon.adapt(item, lookup=r)
  small_icon = icon_api.small()
