# annoying warning from BS4

from logging import Logger, StreamHandler, Formatter
import logging

import PIL  # @UnusedImport
import chardet  # @UnusedImport

FORMAT = "%(name)15s|%(filename)15s:%(lineno)-4s - %(funcName)-15s| %(message)s"


if Logger.root.handlers:  # @UndefinedVariable
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

