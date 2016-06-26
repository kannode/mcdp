# -*- coding: utf-8 -*-
__version__ = '2.0.11'

import logging
from contracts.utils import raise_wrapped
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def suggest_package(name):
    msg = """You could try installing the package using:
    
    sudo apt-get install %s
""" % name
    logger.info(msg)
    
try:
    import numpy
    numpy.seterr('raise')
except ImportError as e:
    logger.error(e)
    suggest_package('python-numpy')
    raise Exception('Numpy not available')

try:
    from PIL import Image
except ImportError as e:
    logger.error(e)
    suggest_package('python-pil')
    msg = 'PIL not available'
    # raise Exception('PIL not available')
    logger.error(msg)
    # raise_wrapped(Exception, e, msg)

try:
    import matplotlib
except ImportError as e:
    logger.error(e)
    suggest_package('python-matplotlib')
    msg = 'Matplotlib not available'
    logger.error(msg)
    # raise_wrapped(Exception, e, 'Matplotlib not available')

try:
    import yaml
except ImportError as e:
    logger.error(e)
    suggest_package('python-yaml')
    msg = 'YAML package not available'
    logger.error(msg)
#     raise Exception('YAML not available')

# command dot -> graphviz

import conf_tools
import decent_params
import decent_logs
import quickapp
