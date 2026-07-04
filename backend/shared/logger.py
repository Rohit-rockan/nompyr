import logging
import sys
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    Enables log aggregators (like Datadog/ELK) to easily index Nompyr errors.
    """
    def format(self, record):
        log_record = {
            "time": datetime.utcnow().isoformat() + "Z",
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logger(name="nompyr_backend"):
    """
    Creates a structured JSON logger.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()
