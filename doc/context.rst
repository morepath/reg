Context-based dispatch
======================

Introduction
------------

Consider this advanced use case for Reg: we have a runtime with
multiple contexts. For each context, you want the dispatch behavior to
be different. Concretely, if you have an application where you can
call a view dispatch function, you want it to execute a different
function and return a different value in each separate context.

The Morepath web framework uses this feature of Reg to allow the
developer to compose a larger application from multiple smaller ones.

You can define application context as a class. This context class
defines dispatch *methods*. When you subclass the context class, you
establish a new context: each subclass has entirely different dispatch
registrations, and shares nothing with its base class.

A Context Class
---------------

Here is a concrete example. First we define a context class we call
``A``, and a ``view`` dispatch method on it:

.. testcode::

  import reg

  class A(object):
      @reg.dispatch_method(
        reg.match_instance('obj'),
        reg.match_key('request_method',
                      lambda self, obj, request: request.request_method))
      def view(self, obj, request):
          return "default"

Note that since ``view`` is a method we define a ``self`` argument.

To have something to view, We define ``Document`` and ``Image``
content classes:

.. testcode::

  class Document(object):
     def __init__(self, text):
         self.text = text

  class Image(object):
      def __init__(self, bytes):
          self.bytes = bytes

We also need a request class:

.. testcode::

  class Request(object):
      def __init__(self, request_method, body=''):
          self.request_method = request_method
          self.body = body

To try this out, we need to create an instance of the context class:

.. testcode::

  a = A()

Before we register anything, we get the default result we defined
in the method:

.. doctest::

  >>> doc = Document('Hello world!')
  >>> a.view(doc, Request('GET'))
  'default'
  >>> a.view(doc, Request('POST', 'new content'))
  'default'
  >>> image = Image('abc')
  >>> a.view(image, Request('GET'))
  'default'

Here are the functions we are going to register:

.. testcode::

  def document_get(obj, request):
      return "Document text is: " + obj.text

  def document_post(obj, request):
      obj.text = request.body
      return "We changed the document"

  def image_get(obj, request):
      return obj.bytes

  def image_post(obj, request):
      obj.bytes = request.body
      return "We changed the image"

We now want to register them with our context. To do so, we need to
access the dispatch function through its class (``A``), not its
instance (``a``). All instances of ``A`` (but not instances of its
subclasses as we will see later) share the same registrations.

We use :func:`reg.methodify` to do the registration, to keep our view
functions the same as when context is not in use. We will see an
example without :func:`reg.methodify` later:

.. testcode::

  from reg import methodify
  A.view.register(methodify(document_get),
                  request_method='GET',
                  obj=Document)
  A.view.register(methodify(document_post),
                  request_method='POST',
                  obj=Document)
  A.view.register(methodify(image_get),
                  request_method='GET',
                  obj=Image)
  A.view.register(methodify(image_post),
                  request_method='POST',
                  obj=Image)

Now that we've registered some functions, we get the expected behavior
when we call ``a.view``:

.. doctest::

  >>> a.view(doc, Request('GET'))
  'Document text is: Hello world!'
  >>> a.view(doc, Request('POST', 'New content'))
  'We changed the document'
  >>> doc.text
  'New content'
  >>> a.view(image, Request('GET'))
  'abc'
  >>> a.view(image, Request('POST', "new data"))
  'We changed the image'
  >>> image.bytes
  'new data'

A new context
-------------

Okay, we associate a dispatch method with a context class, but what is the
point? The point is that we can introduce a new context that has
different behavior now. To do, we subclass ``A``:

.. testcode::

   class B(A):
       pass

At this point the new ``B`` context is empty of specific behavior,
even though it subclasses ``A``:

.. doctest::

  >>> b = B()
  >>> b.view(doc, Request('GET'))
  'default'
  >>> b.view(doc, Request('POST', 'New content'))
  'default'
  >>> b.view(image, Request('GET'))
  'default'
  >>> b.view(image, Request('POST', "new data"))
  'default'

We can now do our registrations. Let's register the same
behavior for documents as we did for ``Context``:

.. testcode::

  B.view.register(methodify(document_get),
                  request_method='GET',
                  obj=Document)
  B.view.register(methodify(document_post),
                  request_method='POST',
                  obj=Document)

But we install *different* behavior for ``Image``:

.. testcode::

  def b_image_get(obj, request):
      return 'New image GET'

  def b_image_post(obj, request):
      return 'New image POST'

  B.view.register(methodify(b_image_get),
                  request_method='GET',
                  obj=Image)
  B.view.register(methodify(b_image_post),
                  request_method='POST',
                  obj=Image)

Calling ``view`` for ``Document`` works as before:

.. doctest::

  >>> b.view(doc, Request('GET'))
  'Document text is: New content'

But the behavior for ``Image`` instances is different in the ``B``
context:

.. doctest::

  >>> b.view(image, Request('GET'))
  'New image GET'
  >>> b.view(image, Request('POST', "new data"))
  'New image POST'

Note that the original context ``A`` is of course unaffected and still
has the behavior we registered for it:

.. doctest::

  >>> a.view(image, Request('GET'))
  'new data'

The idea is that you can create a framework around your base context
class. Where this base context class needs to have dispatch behavior,
you define dispatch methods. You then create different subclasses of
the base context class and register different behaviors for them. This
is what Morepath does with its ``App`` class.

Call method in the same context
-------------------------------

What if in a dispatch implementation you find you need to call another
dispatch method? How to access the context? You can do this by
registering a function that get a context as its first argument. As an
example, we modify our document functions so that ``document_post``
uses the other:

.. testcode::

  def c_document_get(context, obj, request):
      return "Document text is: " + obj.text

  def c_document_post(context, obj, request):
      obj.text = request.body
      return "Changed: " + context.view(obj, Request('GET'))

Now ``c_document_post`` uses the ``view`` dispatch method on the
context. We need to register these methods using
:meth:`reg.Dispatch.register` without :func:`reg.methodify`. This way
they get the context as the first argument. Let's create a new context
and do so:

.. testcode::

  class C(A):
      pass

  C.view.register(c_document_get,
                  request_method='GET',
                  obj=Document)
  C.view.register(c_document_post,
                  request_method='POST',
                  obj=Document)

We now get the expected behavior:

.. doctest::

  >>> c = C()
  >>> c.view(doc, Request('GET'))
  'Document text is: New content'
  >>> c.view(doc, Request('POST', 'Very new content'))
  'Changed: Document text is: Very new content'

You could have used :func:`reg.methodify` for this too, as
``methodify`` inspects the first argument and if it's identical to the
second argument to ``methodify``, it will pass in the context as that
argument.

.. testcode::

  class D(A):
      pass

  D.view.register(methodify(c_document_get, 'context'),
                  request_method='GET',
                  obj=Document)
  D.view.register(methodify(c_document_post, 'context'),
                  request_method='POST',
                  obj=Document)
.. doctest::

  >>> d = D()
  >>> d.view(doc, Request('GET'))
  'Document text is: Very new content'
  >>> d.view(doc, Request('POST', 'Even newer content'))
  'Changed: Document text is: Even newer content'

The default value for the second argument to ``methodify`` is ``app``.
