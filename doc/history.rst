History of Reg
==============

Reg was written by me, Martijn Faassen. The core mapping code was
originally co-authored by Thomas Lotze, though this has since been
subsumed into the generalized predicate architecture.

Reg is a generic dispatch implementation for Python, with support for
multiple dispatch registries in the same runtime. It was originally
heavily inspired by the Zope Component Architecture (ZCA) consisting
of the ``zope.interface`` and ``zope.component`` packages. Reg has
strongly evolved since its inception into a general function dispatch
library. Reg's codebase is completely separate from the ZCA and it has
an entirely different API. At the end I've included a brief history of
the ZCA.

Reg History
-----------

The Reg code went through a bit of history:

The core registry (mapping) code was conceived by Thomas Lotze and
myself as a speculative sandbox project in January of 2010. It was
called ``iface`` then:

http://svn.zope.org/Sandbox/faassen/iface/

In early 2012, I was at a sprint in Nürnberg, Germany organized by
Novareto. Inspired by discussions with the sprint participants,
particularly the Cromlech developers Souheil Chelfouh and Alex Garel,
I created a project called Crom:

https://github.com/faassen/crom

Crom focused on rethinking component and adapter registration and
lookup APIs, but was still based on ``zope.interface`` for its
fundamental ``AdapterRegistry`` implementation and the ``Interface``
metaclass. I worked a bit on Crom after the sprint, but soon I moved
on to other matters.

At the Plone conference held in Arnhem, the Netherlands in October
2012, I gave a lightning talk about Crom. I figured what Crom needed
was a rewrite of the core adapter registry, i.e. what was in the iface
project. In the end of 2012 I mailed Thomas Lotze asking whether I
could merge iface into Crom, and he gave his kind permission.

The core registry code of iface was never quite finished however, and
while the iface code was now in Crom, Crom didn't use it yet. Thus it
lingered some more.

In July 2013 in development work for CONTACT (contact.de), I found
myself in need of clever registries. Crom also had some configuration
code intermingled with the component architecture code and I didn't
want this anymore.

So I reorganized the code yet again into another project, this one:
Reg. I then finished the core mapping code and hooked it up to the
Crom-style API, which I refactored further. For interfaces, I used
Python's ``abc`` module.

For a while during internal development this codebase was called
``Comparch``, but this conflicted with another name so I decided to
call it ``Reg``, short for registry, as it's really about clever
registries more than anything else.

After my first announcement_ of Reg to the world in September 2013 I
got the question why I shouldn't just use PEP 443, which has a generic
function implementation (single dispatch). I started thinking I should
convert Reg to a generic function implementation, as it was already
very close. After talking to some people about this at PyCon DE in
october, I did the refactoring_ to use generic functions throughout
and no interfaces for lookup. I used this version of Reg in Morepath
for about a year.

.. _announcement: http://blog.startifact.com/posts/reg-component-architecture-reimagined.html

.. _refactoring: http://blog.startifact.com/posts/reg-now-with-more-generic.html

In October 2014 I had some experience with using Reg and found some of
its limitations:

* Reg would try to dispatch on *all* non-keyword arguments of a function.
  This is not what is desired in many cases. We need a way to dispatch only
  on specified arguments and leave others alone.

* Reg had an undocumented predicate subsystem used to implement view
  lookup in Morepath. I realized that it could not be properly used to
  dispatch on the class of an instance without reorganizing Reg in a
  major way.

* I realized that such a reorganized predicate system could actually
  be used to generalize the way Reg worked based on how predicates worked.

* This would allow predicates to play along in Reg's caching
  infrastructure, which could then speed up Morepath's view lookups.

* A specific use case to replace class methods caused me to introduce
  ``reg.classgeneric``. This could be subsumed in a generalized
  predicate infrastructure as well.

So in October 2014, I refactored Reg once again in the light of
this. This results in a smaller, more unified codebase that has more
features and is hopefully also faster.

Brief history of Zope Component Architecture
--------------------------------------------

Reg is heavily inspired by ``zope.interface`` and ``zope.component``,
by Jim Fulton and a lot of Zope developers. ``zope.interface`` has a
long history, going all the way back to December 1998, when a
scarecrow interface package was released for discussion:

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
