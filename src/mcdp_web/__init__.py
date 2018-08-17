# -*- coding: utf-8 -*-


# Creating views fails for cython compiled functions
from pyramid.compat import is_unbound_method


def is_unbound_method_cython(f):
    return False


import pyramid

pyramid.compat.is_unbound_method = is_unbound_method_cython

from .main import *
