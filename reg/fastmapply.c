#include <Python.h>

PyCodeObject* get_code(PyObject* callable_obj, PyObject** method_obj_out) {
  PyObject* func_obj;
  PyObject* method_obj = NULL;

  if (PyFunction_Check(callable_obj)) {
    /* function */
    func_obj = callable_obj;
  } else if (PyMethod_Check(callable_obj)) {
    /* method */
    func_obj = PyMethod_Function(callable_obj);
  } else if (PyType_Check(callable_obj)) {
    /* new style class */
    method_obj = PyObject_GetAttrString(callable_obj, "__init__");
    if (PyMethod_Check(method_obj)) {
      func_obj = PyMethod_Function(method_obj);
    } else {
      /* descriptor found, not method, so no __init__ */
      func_obj = NULL;
    }
  } else if (PyClass_Check(callable_obj)) {
    /* old style class */
    method_obj = PyObject_GetAttrString(callable_obj, "__init__");
    if (method_obj != NULL) {
      func_obj = PyMethod_Function(method_obj);
    } else {
      PyErr_SetString(PyExc_TypeError,
                      "Old-style class without __init__ not supported");
      return NULL;
    }
  } else if (PyCFunction_Check(callable_obj)) {
    /* function implemented in C extension */
    PyErr_SetString(PyExc_TypeError,
                    "functions implemented in C are not supported");
    return NULL;
  } else {
    /* new or old style class instance */
    method_obj = PyObject_GetAttrString(callable_obj, "__call__");
    if (method_obj != NULL) {
      func_obj = PyMethod_Function(method_obj);
    } else {
      PyErr_SetString(PyExc_TypeError,
                      "Instance is not callable");
      return NULL;
    }
  }

  // output method parameter
  *method_obj_out = method_obj;

  if (func_obj == NULL) {
    return NULL;
  }
  /* we can determine the arguments now */
  return (PyCodeObject*)PyFunction_GetCode(func_obj);
}

static PyObject*
mapply(PyObject *self, PyObject *args, PyObject* kwargs)
{
  PyObject* callable_obj;
  PyObject* remaining_args;
  PyObject* result;
  PyCodeObject* co;
  PyObject* method_obj = NULL;
  PyObject* new_kwargs = NULL;
  int i;

  if (PyTuple_GET_SIZE(args) < 1) {
    PyErr_SetString(PyExc_TypeError,
                    "mapply() takes at one parameter");
    return NULL;
  }

  callable_obj = PyTuple_GET_ITEM(args, 0);
  remaining_args = PyTuple_GetSlice(args, 1, PyTuple_GET_SIZE(args));

  co = get_code(callable_obj, &method_obj);


  /* an error was raised in get_code */
  if (co == NULL && method_obj == NULL) {
    return NULL;
  }
  /* we did actually get a method, but it wasn't one we could do something
     with; this happens with empty __init__ in new style classes */
  if (co == NULL && method_obj != NULL) {
    goto final;
  }

  /* we have a method_obj but not one we can do anything with as we
     have no co object, must be __init__ without parameters, go to end

     or we called this without keyword arguments

     or this function accepts keyword arguments
  */
  if (co == NULL || kwargs == NULL || co->co_flags & CO_VARKEYWORDS) {
    /* we reuse the existing kwargs, but incref so we can decref symmetrically
       later */
    new_kwargs = kwargs;
    Py_XINCREF(new_kwargs);
    goto final;
  }

  /* create a new keyword argument dict with only the desired args */
  new_kwargs = PyDict_New();

  for (i = 0; i < co->co_argcount; i++) {
    PyObject* name = PyTuple_GET_ITEM(co->co_varnames, i);
    PyObject* value = PyDict_GetItem(kwargs, name);
    if (value != NULL) {
      PyDict_SetItem(new_kwargs, name, value);
    }
  }

 final:
  /* call the underlying function */
  result = PyObject_Call(callable_obj, remaining_args, new_kwargs);
  /* cleanup */
  Py_DECREF(remaining_args);
  Py_XDECREF(new_kwargs); /* can be null */
  Py_XDECREF(method_obj); /* can be null */
  return result;
}

static PyObject*
lookup_mapply(PyObject *self, PyObject *args, PyObject* kwargs)
{
  PyObject* callable_obj;
  PyObject* lookup_obj;
  PyObject* remaining_args;
  PyObject* result;
  PyCodeObject* co;
  PyObject* method_obj = NULL;
  int i, has_lookup = 0, cleanup_dict = 0;

  if (PyTuple_GET_SIZE(args) < 2) {
    PyErr_SetString(PyExc_TypeError,
                    "lookup_mapply() takes at least two parameters");
    return NULL;
  }

  callable_obj = PyTuple_GET_ITEM(args, 0);
  lookup_obj = PyTuple_GET_ITEM(args, 1);
  remaining_args = PyTuple_GetSlice(args, 2, PyTuple_GET_SIZE(args));

  co = get_code(callable_obj, &method_obj);

  /* an error was raised in get_code */
  if (co == NULL && method_obj == NULL) {
    return NULL;
  }
  /* we did actually get a method, but it wasn't one we could do something
     with; this happens with empty __init__ in new style classes */
  if (co == NULL && method_obj != NULL) {
    goto final;
  }

  if (!(co->co_flags & CO_VARKEYWORDS)) {
    for (i = 0; i < co->co_argcount; i++) {
      PyObject* name = PyTuple_GET_ITEM(co->co_varnames, i);
      if (strcmp(PyString_AS_STRING(name), "lookup") == 0) {
        has_lookup = 1;
        break;
      }
    }
    if (has_lookup) {
      if (kwargs == NULL) {
        kwargs = PyDict_New();
        cleanup_dict = 1;
      }
      PyDict_SetItem(kwargs, PyString_FromString("lookup"), lookup_obj);
    }
  }
 final:
  result = PyObject_Call(callable_obj, remaining_args, kwargs);
  Py_DECREF(remaining_args);
  if (cleanup_dict) {
    Py_DECREF(kwargs);
  }
  Py_XDECREF(method_obj);
  return result;
}

static PyMethodDef FastMapplyMethods[] = {
  {"lookup_mapply", (PyCFunction)lookup_mapply, METH_VARARGS | METH_KEYWORDS,
   "apply with optional lookup parameter"},
  {"mapply", (PyCFunction)mapply, METH_VARARGS | METH_KEYWORDS,
   "mapply"},

  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initfastmapply(void)
{
  (void) Py_InitModule("fastmapply", FastMapplyMethods);
}
