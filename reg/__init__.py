# flake8: noqa
#from .registry import Registry, CachingKeyLookup, Lookup
from .dispatch import dispatch
from .mapply import mapply
from .arginfo import arginfo
from .argextract import KeyExtractor
from .sentinel import Sentinel, NOT_FOUND
from .error import RegistrationError, KeyExtractorError
from .predicate import (Predicate, PredicateRegistry, KeyIndex, ClassIndex,
                        key_predicate, class_predicate,
                        match_key, match_instance, match_argname,
                        match_class, CachingKeyLookup, Lookup)
