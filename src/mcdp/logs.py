from logging import Logger, StreamHandler, Formatter
import logging

FORMAT = "%(name)15s|%(filename)15s:%(lineno)-4s - %(funcName)-15s| %(message)s"

logging.basicConfig(format=FORMAT)

if Logger.root.handlers:  # @UndefinedVariable
    for handler in Logger.root.handlers:  # @UndefinedVariable
        if isinstance(handler, StreamHandler):
            formatter = Formatter(FORMAT)
            handler.setFormatter(formatter)
else:
    logging.basicConfig(format=FORMAT)

logger = logging.getLogger('mcdp')
logger.setLevel(logging.DEBUG)

# temporary stuff - use instead of print()
logger_tmp = logger.getChild('tmp')
logger_access = logger.getChild('access')
logger_access.setLevel(logging.INFO)
logger_performance = logger.getChild('p')

logger_web_resource_tree = logger.getChild('r')
logger_web_resource_tree.setLevel(logging.FATAL)

