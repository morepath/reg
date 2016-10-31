API
===

.. py:module:: reg

Dispatch functions
------------------

.. autofunction:: dispatch

.. autoclass:: Dispatch
  :members:

.. autofunction:: match_key

.. autofunction:: match_instance

.. autofunction:: match_class

.. autoclass:: LookupEntry
   :members:

.. autoclass:: DictCachingKeyLookup
   :members:

.. autoclass:: LruCachingKeyLookup
   :members:

Context-specific dispatch methods
---------------------------------

.. autofunction:: dispatch_method

.. autoclass:: DispatchMethod
  :members:
  :inherited-members:

.. autofunction:: clean_dispatch_methods

.. autofunction:: methodify

Errors
------

.. autoexception:: RegistrationError

Argument introspection
----------------------

.. autofunction:: arginfo

Low-level predicate support
---------------------------

Typically, you'd be using :func:`reg.match_key`,
:func:`reg.match_instance`, and :func:`reg.match_class` to define
predicates.  Should you require finer control, you can use the
following classes:

.. autoclass:: Predicate
   :members:

.. autoclass:: ClassIndex
   :members:

.. autoclass:: KeyIndex
   :members:
