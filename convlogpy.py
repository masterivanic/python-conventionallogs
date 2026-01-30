import functools
import inspect
import json
import logging
from pathlib import Path
import sys
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Union

type LogMessage = Union[str, int]

class ConflictKeyError(Exception):
    pass

class VariableNotFoundException(Exception):
    pass

class SingletonType(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Formatter(logging.Formatter):
    def __init__(self,  func:Callable, *args, **kwargs,):
        super().__init__(*args, **kwargs)
        self._formatter = func

    def format(self, record):
        try:
            log_entry = self._formatter(record)
            return json.dumps(log_entry)
        except Exception:
            return json.dumps({
                "severity": "ERROR",
                "scope": "logger",
                "message": f"Failed to format log record: {record.getMessage()}",
                "timestamp": datetime.now().isoformat() + "Z"
            })

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

    def __init__(self, level=logging.DEBUG, scope="application", name:str = None, console = True):
        super().__init__(level)
        self.scope = scope
        self._logger = logging.getLogger(__name__ or name)
        self._logger.setLevel(level)
        self._logger.handlers = [] # since all the lower level loggers at module level eventually forward their messages to its handlers

        if console:
            self._logger.addHandler(self)
        else:
            self._file_handlers: Dict[str, logging.Handler] = {}
            self._formatter = Formatter(func=self._format_record)
            self.setFormatter(self._formatter)
    
    def add_file_handler(
        self,
        filepath: Union[str, Path],
        level: Optional[int] = None,
        delay: bool = False
    ) -> None:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(
            filename=str(filepath),
            mode="a",
            delay=delay
        )
        
        handler.setLevel(self._logger.level or level)
        handler.setFormatter(self._formatter)
        self._logger.addHandler(handler)
        self._file_handlers[str(filepath)] = handler

    def add_rotating_file_handler(
        self,
        filepath: Union[str, Path],
        max_bytes: int = 30 * 1024 * 1024,
        backup_count: int = 5,
        level: Optional[int] = None,
        encoding: str = 'utf-8',
        delay: bool = False
    ) -> None:
        """
        Add a rotating file handler for log rotation.
        
        Args:
            filepath: Path to the log file
            max_bytes: Maximum file size before rotation limit by default to 30 Mb
            backup_count: Number of backup files to keep
            level: Logging level for this handler
            encoding: File encoding
            delay: If True, file opening is deferred until first log
        """
        from logging.handlers import RotatingFileHandler
        
        filepath = Path(filepath)
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            filename=str(filepath),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
            delay=delay
        )
        
        handler.setLevel(self._logger.level or level)
        handler.setFormatter(self._formatter)
        self._logger.addHandler(handler)
        self._file_handlers[str(filepath)] = handler


    def add_timed_rotating_file_handler(
        self,
        filepath: Union[str, Path],
        when: str = 'midnight',
        interval: int = 1,
        backup_count: int = 7,
        delay: bool = False,
        utc: bool = False
    ) -> None:
        """
        Add a time-based rotating file handler.
        
        Args:
            filepath: Path to the log file
            when: When to rotate ('S', 'M', 'H', 'D', 'W0'-'W6', 'midnight')
            interval: Rotation interval
            backup_count: Number of backup files to keep
            level: Logging level for this handler
            encoding: File encoding
            delay: If True, file opening is deferred until first log
            utc: Use UTC time for rotation
        """
        from logging.handlers import TimedRotatingFileHandler
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        handler = TimedRotatingFileHandler(
            filename=str(filepath),
            when=when,
            interval=interval,
            backupCount=backup_count,
            delay=delay,
            utc=utc
        )
        
        handler.setLevel(self._logger.level)
        handler.setFormatter(self._formatter)
        self._logger.addHandler(handler)
        self._file_handlers[str(filepath)] = handler
        
   
    def remove_file_handler(self, filepath: Union[str, Path]) -> bool:
        if filepath in self._file_handlers:
            handler = self._file_handlers[str(filepath)]
            self._logger.removeHandler(handler)
            handler.close()
            del self._file_handlers[str(filepath)]
            return True
        return False
    
    def remove_all_file_handlers(self) -> None:
        for _, handler in list(self._file_handlers.items()):
            self._logger.removeHandler(handler)
            handler.close()
        
        self._file_handlers.clear()
        
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
            attrs = record.__dict__.keys() & extra_fields.keys()
            if bool(attrs): # https://docs.python.org/3/library/logging.html#logrecord-attributes
                raise ConflictKeyError("extra fields dictionary passed in extra should not clash with record keys %s", attrs)


        if record.levelno is logging.ERROR:
            if 'fields' in log_entry.keys():
                log_entry['fields'].update(
                    {
                        "module": record.module,
                        "function": record.funcName,
                        "line": record.lineno,
                    }
                )
            else:
                log_entry["fields"] = {
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                }
        return log_entry
    
    def debug(self, msg:LogMessage, **kwargs) -> None:
        self._log(logging.DEBUG, msg, **kwargs)

    def debug_vars(self, variables:list = None, stringify:bool= False) -> Callable[..., Any]:
        """
        help to debug variable of arguments of a given function
        """

        variables = variables or []
        locals_vars = {}
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            signature = inspect.signature(func)
            arg_names = list(func.__code__.co_varnames)[:func.__code__.co_argcount]
        
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                bound = signature.bind(*args, **kwargs)
                bound.apply_defaults()
                        
                arg = dict(zip(arg_names, [bound.args[i] for i in range(len(arg_names))]))
                self.info(f"Arguments of function {func.__name__} passed in input", **arg)

                def profiler(frame, event, arg): # https://stackoverflow.com/questions/40674861/how-to-trace-builtin-functions-in-python
                    """
                        #https://docs.python.org/3/library/sys.html#sys.setprofile
                    """
                    if event == 'return' and frame.f_code.co_name == func.__name__:
                        locals_vars.update(frame.f_locals)
                        for argument in arg_names:
                            locals_vars.pop(argument, None)

                        filter_vars = list(filter(lambda x: x in locals_vars, variables))
                        result = {v : locals_vars[v] for v in filter_vars}
                        self.debug(f"Variables of function {func.__name__}", **result)
                    return profiler
                sys.setprofile(profiler)
                try:
                    return func(*args, **kwargs)
                finally:
                    sys.setprofile(None)
            return wrapper
        return decorator


    def info(self, msg:LogMessage, **kwargs) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg:LogMessage, **kwargs) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg:LogMessage, **kwargs) -> None:
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg:LogMessage, **kwargs) -> None:
        self._log(logging.CRITICAL, msg, **kwargs)

    def exception(self, msg: LogMessage, **kwargs) -> None:
        self._log(logging.ERROR, msg, **kwargs)

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
