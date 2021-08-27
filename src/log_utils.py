import logging

# Redirect warnings from stderr to Python standard logging (e.g., warnings
# raised by `warnings.warn()` will be directly write to the log file)
logging.captureWarnings(True)


class LogUtil(object):
    def __init__(self, log_file, filemode='w'):
        fmt = logging.Formatter(fmt='%(asctime)-15s: %(message)s',
                                datefmt='[%Y-%m-%d %H:%M:%S]')
        handler = logging.FileHandler(log_file, mode=filemode)
        handler.setFormatter(fmt)
        logger = logging.getLogger('py.warnings')
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        self.logger = logger

    def info(self, message):
        self.logger.info(message)

    def error(self, exception):
        self.logger.error(exception, exc_info=True)
