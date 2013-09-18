Using Reg
=========

Introduction
------------

Reg introduces a bunch of clever registries that can help you build
very flexible pluggability systems for your codebase. With Reg you can:

* look up a registered object that provides a certain interface

* do this lookup by itself, or for one or more objects

* adapt an object to another with a specific interface

* look up a registered object according to other criteria (predicates)

Reg is very much aware of classes and inheritance. It provides an approach
to do `multiple dispatch`_ in Python.

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

What have we gained?
--------------------

We could've just imported ``emailer`` and that would've been a lot
easier! That's true. What we've gained is the ability to register a
service for a library or application (in this case sending email) and
the ability to change what service is used without having to change
the code that uses that service. This is at the cost of some
indirection.

