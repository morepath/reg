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

Predicate Registry
------------------

.. autoclass:: PredicateRegistry
   :members:

.. autoclass:: Predicate
   :members:

.. autoclass:: ClassIndex
   :members:

.. autoclass:: KeyIndex
   :members:

.. autofunction:: key_predicate

.. autofunction:: class_predicate
