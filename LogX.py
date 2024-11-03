import logging

# Define color codes
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[31m',   # Red
        'WARNING': '\033[33m', # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[1;31m', # Bold Red
        'SENT': '\033[34m',   # Blue
        'RECEIVED': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_fmt = f"{self.COLORS.get(record.levelname, self.RESET)}%(message)s{self.RESET}"
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Initialize logging with the colored formatter
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Define custom log levels
logging.addLevelName(25, "RECEIVED")
logging.addLevelName(26, "SENT")

def log_received(message):
    logger.log(25, message)

def log_sent(message):
    logger.log(26, message)

# Example function to log a message
def log_message(message):
    logger.info(message)
