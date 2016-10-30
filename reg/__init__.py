# flake8: noqa
from .dispatch import dispatch, Dispatch, LookupEntry
from .context import (dispatch_method, DispatchMethod,
                      methodify, clean_dispatch_methods)
from .arginfo import arginfo
from .error import RegistrationError
from .predicate import (Predicate, KeyIndex, ClassIndex,
                        match_key, match_instance, match_class)
from .cache import DictCachingKeyLookup, LruCachingKeyLookup
