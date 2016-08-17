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

.. autofunction:: match_argname

.. autofunction:: match_class

.. autoclass:: CachingKeyLookup
   :members:

Context-specific dispatch methods
---------------------------------

.. autofunction:: dispatch_method

.. autoclass:: MethodDispatch
  :members:

.. autofunction:: install_auto_method

.. autofunction:: clean_dispatch_methods

Errors
------

.. autoexception:: RegistrationError

.. autoexception:: KeyExtractorError

Argument introspection
----------------------

.. autofunction:: mapply

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
