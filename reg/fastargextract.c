#include <Python.h>

#if PY_MAJOR_VERSION >= 3
#define IS_PY3
#endif

PyObject* get_function_object(PyObject* callable_obj,
                              PyObject** method_obj_out,
                              int* init_no_args) {
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
#ifndef IS_PY3
    /* in Python 2 __init__ is a method */
    if (PyMethod_Check(method_obj)) {
      func_obj = PyMethod_Function(method_obj);
    } else {
      /* something else found, not method, so no __init__ */
      func_obj = NULL;
      *init_no_args = 1;
    }
#else
    /* in Python 3 __init__ is a function */
    if (PyFunction_Check(method_obj)) {
      func_obj = method_obj;
    } else {
      /* something else found, not function, so no __init__ */
      func_obj = NULL;
      *init_no_args = 1;
    }
#endif

#ifndef IS_PY3
    /* old style classes only exist in Python 2 */
  } else if (PyClass_Check(callable_obj)) {
    /* old style class */
    method_obj = PyObject_GetAttrString(callable_obj, "__init__");
    if (method_obj != NULL) {
      func_obj = PyMethod_Function(method_obj);
    } else {
      PyErr_SetString(PyExc_TypeError,
                    "old-style classes without __init__ not supported");
      return NULL;
    }
#endif
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
#ifndef IS_PY3
      /* old style classes only exist in Python 2 */
      if (PyInstance_Check(callable_obj)) {
        PyErr_SetString(PyExc_AttributeError,
                        "Instance has no __call__ method");
      } else {
#endif
        PyErr_SetString(PyExc_TypeError,
                        "Instance is not callable");
#ifndef IS_PY3
      }
#endif
      return NULL;
    }
  }

  // output method parameter used for cleanup
  *method_obj_out = method_obj;

  return func_obj;
}

static PyObject*
argextract(PyObject *self, PyObject *args, PyObject* kwargs)
{
  if (PyTuple_GET_SIZE(args) < 2) {
    PyErr_SetString(PyExc_TypeError,
                    "argextract() takes at least two parameters");
    return NULL;
  }

  PyObject* callable_obj = PyTuple_GET_ITEM(args, 0);
  PyObject* names = PyTuple_GET_ITEM(args, 1);
  if (!PyTuple_Check(names)) {
    PyErr_SetString(PyExc_TypeError,
                    "second argument must be a tuple of names");
    return NULL;
  }
  PyObject* not_found = PyTuple_GET_ITEM(args, 2);

  PyObject* remaining_args = PyTuple_GetSlice(args, 3,
                                              PyTuple_GET_SIZE(args));

  int init_no_args = 0;
  PyObject* method_obj = NULL;
  PyObject* fo = get_function_object(callable_obj, &method_obj, &init_no_args);
  PyObject* defaults = PyFunction_GetDefaults(fo);
  PyCodeObject* co = (PyCodeObject*)PyFunction_GetCode(fo);

  PyObject* result = PyDict_New();

  Py_ssize_t last_pos = -1;
  Py_ssize_t kw_args = 0;

  PyObject* varargs_name = NULL;
  PyObject* kwargs_name = NULL;
  Py_ssize_t varargs_pos = co->co_argcount;
  Py_ssize_t kwargs_pos = varargs_pos;
  if (co->co_flags & CO_VARARGS) {
    varargs_name = PyTuple_GET_ITEM(co->co_varnames, varargs_pos);
    kwargs_pos++;
  }
  if (co->co_flags & CO_VARKEYWORDS) {
    kwargs_name = PyTuple_GET_ITEM(co->co_varnames, kwargs_pos);
  }

  for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(names); i++) {
    PyObject* name = PyTuple_GET_ITEM(names, i);
    if (varargs_name && PyObject_RichCompareBool(name, varargs_name, Py_EQ)) {
      continue;
    }
    if (kwargs_name && PyObject_RichCompareBool(name, kwargs_name, Py_EQ)) {
      continue;
    }
    if (kwargs != NULL) {
      PyObject* value = PyDict_GetItem(kwargs, name);
      // if we have the value in keyword arguments, we set it in the result
      if (value != NULL) {
        PyDict_SetItem(result, name, value);
        kw_args++;
        continue;
      }
    }
    for (Py_ssize_t j = 0; j < co->co_argcount; j++) {
      PyObject* argname = PyTuple_GET_ITEM(co->co_varnames, j);
      if (PyObject_RichCompareBool(name, argname, Py_EQ)) {
        PyObject* arg_value = NULL;
        // the value is in the remaining arguments
        if (j < PyTuple_GET_SIZE(remaining_args)) {
          arg_value = PyTuple_GET_ITEM(remaining_args, j);
          if (j > last_pos) {
            last_pos = j;
          }
        } else {
          Py_ssize_t default_pos = j - (PyTuple_GET_SIZE(remaining_args)
                                        + kw_args);
          // if we don't have the value, get it from the varargs
          if (defaults && (default_pos < PyTuple_GET_SIZE(defaults))) {
            arg_value = PyTuple_GET_ITEM(defaults, default_pos);
            if (j > last_pos) {
              last_pos = j;
            }
          } else {
            arg_value = not_found;
          }
        }
        PyDict_SetItem(result, name, arg_value);
      }
    }
  }

  // set keywords arguments in result
  if (co->co_flags & CO_VARKEYWORDS) {
    PyObject *key, *value;
    PyObject* keywords = PyDict_New();
    Py_ssize_t pos = 0;
    if (kwargs != NULL) {
      while (PyDict_Next(kwargs, &pos, &key, &value)) {
        if (PyDict_Contains(result, key)) {
          continue;
        }
        PyDict_SetItem(keywords, key, value);
      }
    }
    PyDict_SetItem(result, kwargs_name, keywords);
  }
  // set varargs in result last
  if (co->co_flags & CO_VARARGS) {
    PyDict_SetItem(result, varargs_name,
                   PyTuple_GetSlice(remaining_args,
                                    last_pos + 1,
                                    PyTuple_GET_SIZE(remaining_args)));
  }

  /* cleanup */
  Py_DECREF(remaining_args);
  Py_XDECREF(method_obj);  /* can be null */
  return result;
}

static PyMethodDef ArgextractMethods[] = {
  {"argextract", (PyCFunction)argextract, METH_VARARGS | METH_KEYWORDS,
   "argextract"},

  {NULL, NULL, 0, NULL}
};

#ifdef IS_PY3
static struct PyModuleDef moduledef = {
  PyModuleDef_HEAD_INIT,
  "fastargextract",
  NULL,
  0,
  ArgextractMethods,
  NULL,
  NULL,
  NULL,
  NULL
};
#endif

PyMODINIT_FUNC
#ifndef IS_PY3
initfastargextract(void)
#else
  PyInit_fastargextract(void)
#endif
{
#ifndef IS_PY3
  (void) Py_InitModule("fastargextract", ArgextractMethods);
#else
  return PyModule_Create(&moduledef);
#endif
}
