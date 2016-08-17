# flake8: noqa
from .dispatch import (dispatch, dispatch_method, Dispatch, DispatchMethod,
                       install_auto_method, clean_dispatch_methods)
from .mapply import mapply
from .arginfo import arginfo
from .argextract import KeyExtractor
from .sentinel import Sentinel, NOT_FOUND
from .error import RegistrationError, KeyExtractorError
from .predicate import (Predicate, PredicateRegistry, KeyIndex, ClassIndex,
                        key_predicate, class_predicate,
                        match_key, match_instance, match_argname,
                        match_class, CachingKeyLookup)
