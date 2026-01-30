import functools
import inspect
import json
import logging
import sys
from datetime import datetime
from typing import Any, Callable, Dict, Union

type LogMessage = Union[str, int]

class ConflictKeyError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class VariableNotFoundException(Exception):
    def __init__(self, *args):
        super().__init__(*args)

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
        self.decorated = False

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

                        filter_arg = list(filter(lambda x: x in locals_vars, variables))
                        final_dict = {v : locals_vars[v] for v in filter_arg}
                        self.debug(f"Variables of function {func.__name__}", **final_dict)
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
