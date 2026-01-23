import json
import logging
import sys
from datetime import datetime
from typing import Any
from typing import Dict


class SingletonType(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ConvLogPy(logging.Handler, metaclass=SingletonType):
    """
    ConvLogPy default class
    accordintg to [conventionnal commit](https://www.conventionallogs.org/en/v0.0.1/).

    e.g:
        ```json
        {
            "severity": "DEBUG",
            "scope": "web-app",
            "message": "user was cached",
            "timestamp": "2022-05-14T14:16:15+00:00"
        }
        ```
    logger = PyLogger(scope="my-scope")

    logger.info("User login successful", user_id=123, ip="192.168.1.1")
    """

    def __init__(self, level=logging.DEBUG, scope="application", name:str = None):
        super().__init__(level)
        self.scope = scope
        self._logger = logging.getLogger(__name__ or name)
        self._logger.setLevel(level)
        self._logger.addHandler(self) # since all the lower level loggers at module level eventually forward their messages to its handlers
        self._logger.handlers = [self]

    def emit(self, record: logging.LogRecord):
        try:
            log_entry = self._format_record(record)
            msg = json.dumps(log_entry)
            self.stream = sys.stdout
            self.stream.write(msg + "\n")
            self.flush()
        except Exception:
            self.handleError(record)

    def _format_record(self, record: logging.LogRecord) -> Dict[str, Any]:
        severity_map = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "CRITICAL",
        }
        extra_fields = {}

        if hasattr(record, "extra") and record.extra:
            extra_fields.update(record.extra)

        log_entry = {
            "severity": severity_map.get(record.levelno, "INFO"),
            "scope": getattr(record, "scope", self.scope),
            "message": record.getMessage(),
            "timestamp": datetime.now().isoformat() + "Z",
        }

        if extra_fields:
            log_entry["fields"] = extra_fields

        if record.levelno is logging.ERROR:
            log_entry.update(
                {
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                }
            )

        return log_entry

    def debug(self, msg: str, **kwargs) -> None:
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs) -> None:
        self._log(logging.CRITICAL, msg, **kwargs)

    def _log(self, level: int, msg: str, **kwargs) -> None:
        import inspect

        extra = kwargs.copy()
        scope = kwargs.get("scope", self.scope)

        frame = inspect.currentframe().f_back.f_back
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno

        record = self._logger.makeRecord(
            name=self._logger.name,
            level=level,
            fn=filename,
            lno=lineno,
            msg=msg,
            args=(),
            exc_info=None,
            sinfo=None,
        )
        record.scope = scope
        setattr(record, "extra", extra)
        self._logger.handle(record)