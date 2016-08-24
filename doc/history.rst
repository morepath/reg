History of Reg
==============

Reg was written by Martijn Faassen. The core mapping code was
originally co-authored by Thomas Lotze, though this has since been
subsumed into the generalized predicate architecture. After a few
years of use, Stefano Taschini initiated a large refactoring and API
redesign.

Reg is a predicate dispatch implementation for Python, with support
for multiple dispatch registries in the same runtime. It was
originally heavily inspired by the Zope Component Architecture (ZCA)
consisting of the ``zope.interface`` and ``zope.component``
packages. Reg has strongly evolved since its inception into a general
function dispatch library. Reg's codebase is completely separate from
the ZCA and it has an entirely different API. At the end I've included
a brief history of the ZCA.

The primary use case for Reg has been the Morepath_ web framework,
which uses it heavily.

.. _Morepath: http://morepath.readthedocs.io

Reg History
-----------

The Reg code went through a quite bit of history as our insights
evolved.

iface
~~~~~

The core registry (mapping) code was conceived by Thomas Lotze and
Martijn Faassen as a speculative sandbox project in January
of 2010. It was called ``iface`` then:

http://svn.zope.org/Sandbox/faassen/iface/

This registry was instrumental in getting Reg started, but was
subsequently removed in a later refactoring.

crom
~~~~

In early 2012, Martijn was at a sprint in Nürnberg, Germany organized
by Novareto. Inspired by discussions with the sprint participants,
particularly the Cromlech developers Souheil Chelfouh and Alex Garel,
Martijn created a project called Crom:

https://github.com/faassen/crom

Crom focused on rethinking component and adapter registration and
lookup APIs, but was still based on ``zope.interface`` for its
fundamental ``AdapterRegistry`` implementation and the ``Interface``
metaclass. Martijn worked a bit on Crom after the sprint, but soon
moved on to other matters.

iface + crom
~~~~~~~~~~~~

At the Plone conference held in Arnhem, the Netherlands in October
2012, Martijn gave a lightning talk about Crom, which was received
positively, which reignited his interest. In the end of 2012 Martijn
mailed Thomas Lotze to ask to merge iface into Crom, and he gave his
kind permission.

The core registry code of iface was never quite finished however, and
while the iface code was now in Crom, Crom didn't use it yet. Thus it
lingered some more.

ZCA-style Reg
~~~~~~~~~~~~~

In July 2013 in development work for CONTACT (contact.de), Martijn
found himself in need of clever registries. Crom also had some
configuration code intermingled with the component architecture code,
and Martijn wanted to separate this out.

So Martijn reorganized the code yet again into another project, this
one: Reg. Martijn then finished the core mapping code and hooked it up
to the Crom-style API, which he refactored further. For interfaces, he
used Python's ``abc`` module.

For a while during internal development this codebase was called
``Comparch``, but this conflicted with another name so he decided to
call it ``Reg``, short for registry, as it's really about clever
registries more than anything else.

This version of Reg was still very similar in concepts to the Zope
Component Architecture, though it used a streamlined API. This
streamlined API lead to further developments.

Generic dispatch
~~~~~~~~~~~~~~~~

After Martijn's first announcement_ of Reg to the world in September
2013 he got a question why it shouldn't just use PEP 443, which has a
generic function implementation (single dispatch). This lead to the
idea of converting Reg into a generic function implementation (with
multiple dispatch), as it was already very close. After talking to
some people about this at PyCon DE in october, Martijn did the
refactoring_ to use generic functions throughout and no interfaces for
lookup. Martijn then used this version of Reg in Morepath for about a
year.

.. _announcement: http://blog.startifact.com/posts/reg-component-architecture-reimagined.html

.. _refactoring: http://blog.startifact.com/posts/reg-now-with-more-generic.html

Predicate dispatch
~~~~~~~~~~~~~~~~~~

In October 2014 Martijn had some experience with using Reg and found
some of its limitations:

* Reg would try to dispatch on *all* non-keyword arguments of a function.
  This is not what is desired in many cases. We need a way to dispatch only
  on specified arguments and leave others alone.

* Reg had an undocumented predicate subsystem used to implement view
  lookup in Morepath. A new requirement lead to the requirement to
  dispatch on the class of an instance, and while Reg's generic
  dispatch system could do it, the predicate subsystem could
  not. Enabling this required a major reorganization of Reg.

* Martijn realized that such a reorganized predicate system could
  actually be used to generalize the way Reg worked based on how
  predicates worked.

* This would allow predicates to play along in Reg's caching
  infrastructure, which could then speed up Morepath's view lookups.

* A specific use case to replace class methods caused me to introduce
  ``reg.classgeneric``. This could be subsumed in a generalized
  predicate infrastructure as well.

So in October 2014, Martijn refactored Reg once again in the light of
this, generalizing the generic dispatch further to `predicate
dispatch`_, and replacing the iface-based registry. This refactoring
resulted in a smaller, more unified codebase that has more features
and was also faster.

.. _`predicate dispatch`: https://en.wikipedia.org/wiki/Predicate_dispatch

Removing implicitness and inverting layers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reg used an implicit ``lookup`` system to find the current registry to
use for dispatch. This allows Morepath to compose larger applications
out of smaller registries, each with their own dispatch context. As an
alternative to the implicit system, you could also pass in a custom
``lookup`` argument to the function to indicate the current registry.

In 2016 Stefano Taschini started pushing on Morepath's use of dispatch
functions and their implicit nature. Subsequent discussions with
Martijn led to the insight that if we approached dispatch functions as
dispatch *methods* on a context class (the Morepath application), we
could get rid of the implicit behavior altogether, while gaining
performance as we'd use Python's method mechanism.

In continuing discussions, Stefano also suggested that there was no
need for Reg in cases where the dispatch behavior of Reg was not
needed. This led to the insight that this non-dispatch behavior could
be installed as methods directly on the context class.

Stefano also proposed that Reg could be internally simplified if we
made the multiple registry behavior less central to the
implementation, and let each dispatch function maintain its own
registry. Stefano and Martijn then worked on an implementation where
the dispatch method behavior is layered on top of a simpler dispatch
function layer.

Brief history of Zope Component Architecture
--------------------------------------------

Reg is heavily inspired by ``zope.interface`` and ``zope.component``,
by Jim Fulton and a lot of Zope developers, though Reg has undergone a
significant evolution since then. ``zope.interface`` has a long
history, going all the way back to December 1998, when a scarecrow
interface package was released for discussion:

http://old.zope.org/Members/jim/PythonInterfaces/Summary/

http://old.zope.org/Members/jim/PythonInterfaces/Interface/

A later version of this codebase found itself in Zope, as ``Interface``:

http://svn.zope.org/Zope/tags/2-8-6/lib/python/Interface/

A new version called zope.interface was developed for the Zope 3
project, somewhere around the year 2001 or 2002 (code historians,
please dig deeper and let me know). On top of this a zope.component
library was constructed which added registration and lookup APIs on
top of the core zope.interface code.

zope.interface and zope.component are widely used as the core of the
Zope 3 project. zope.interface was adopted by other projects, such as
Zope 2, Twisted, Grok, BlueBream and Pyramid.
