import sys
import logging
from loguru import logger
from typing import Optional
from types import FrameType
from redis import RedisError

class InterceptHandler(logging.Handler):
    """Setups a loging handler for uvicorn and FastAPI.

    Args:
        logging (logging.Handler)
    """
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record.

        Args:
            record (LogRecord): Logging record
        """
        
        level: str | int
        frame: Optional[FrameType]
        depth: int
        
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        
        # Find caller from where originated the logged message
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

class HTTPXLogger():
    """Logger adapter for HTTPX."""
    
    async def log_request(self, request) -> None:
        """Logs HTTPX requests
        
        Returns:
            None
        """
        
        logger.info(f"[HTTPX] Request: {request.method} {request.url} - Waiting for response")
        
    async def log_response(self, response) -> None:
        """Logs HTTPX responses
        
        Returns:
            None
        """
        request = response.request
        
        logger.info(f"[HTTPX] Response: {request.method} {request.url} - Status: {response.status_code} {response.reason_phrase}")

class InternalCacheLogger:
    async def log(self, operation: str, result: RedisError | None = None, key: str = "",) -> None:
        """Logs internal cache operations
        
        Args:
            operation (str): Operation name
            key (str): Key used in the operation
        """
        if type(result) is RedisError:
            logger.error(f"[InternalCache] REDIS {operation} - Failed with error: {result}")
        else:
            logger.info(f"[InternalCache] REDIS {operation} {key} - OK")

def setup_logging(LOG_LEVEL: str, JSON_LOGS: bool) -> None:
    
    """Setup logging for uvicorn and FastAPI."""
    
    # intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(LOG_LEVEL)

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # configure loguru
    logger.configure(handlers=[{"sink": sys.stdout, "serialize": JSON_LOGS}])