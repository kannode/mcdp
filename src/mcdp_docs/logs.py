# -*- coding: utf-8 -*-
# annoying warning from BS4

import logging
from logging import Logger, StreamHandler, Formatter

FORMAT = "%(name)15s|%(filename)15s:%(lineno)-4s - %(funcName)-15s| %(message)s"

# noinspection PyUnresolvedReferences
if Logger.root.handlers:  # @UndefinedVariable
    # noinspection PyUnresolvedReferences
    for handler in Logger.root.handlers:  # @UndefinedVariable
        if isinstance(handler, StreamHandler):
            formatter = Formatter(FORMAT)
            handler.setFormatter(formatter)
else:
    logging.basicConfig(format=FORMAT)


logger = logging.getLogger('mcdp-docs')
logger.setLevel(logging.DEBUG)

logging.getLogger("chardet.universaldetector").setLevel(logging.CRITICAL)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.CRITICAL)

