# flake8: noqa
from .implicit import implicit
from .registry import Registry, CachingKeyLookup, Lookup
from .dispatch import dispatch, dispatch_external_predicates
from .mapply import mapply
from .arginfo import arginfo
from .argextract import KeyExtractor
from .sentinel import Sentinel, NOT_FOUND
from .error import RegistrationError, KeyExtractorError, NoImplicitLookupError
from .predicate import (Predicate, PredicateRegistry, KeyIndex, ClassIndex,
                        key_predicate, class_predicate,
                        match_key, match_instance, match_argname,
                        match_class)
