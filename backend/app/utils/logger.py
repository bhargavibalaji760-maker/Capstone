import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name: str = "meditrial", log_file: str = "app.log", level=logging.INFO):
    """
    Configures a structured logger with both console and file output.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Formatting
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (Rotating)
    try:
        # Ensure log directory exists
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, log_file), 
            maxBytes=10*1024*1024, # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")

    return logger

# Default instance
logger = setup_logger()
module_logger = lambda name: setup_logger(name)
