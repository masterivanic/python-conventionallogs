# ConvLogPy

`ConvLogPy` is a lightweight JSON logger built on top of Python's standard `logging` module. It outputs structured logs to `stdout` and/or files, making them easy to parse, search, and aggregate in modern log management systems.

## Features

- **Singleton** logger instance per process to ensure consistent configuration
- JSON-formatted logs with:
  - `severity`
  - `scope`
  - `message`
  - `timestamp` (ISO 8601, UTC with `Z` suffix)
- Optional custom fields under `fields` (e.g. `user_id`, `ip`)
- Automatic enrichment of error logs with:
  - `module`
  - `function`
  - `line`
- **Flexible file logging** with multiple handler types:
  - Standard file handler
  - Size-based rotating file handler
  - Time-based rotating file handler
- **Log rotation** with configurable limits
- **Directory auto-creation** for log files
- **Variable debugging** decorator for function-level inspection

## Installation

```bash
pip install ConvLogPy
```

## Quick Start

### Basic Example

```python
from convlogpy import ConvLogPy

logger = ConvLogPy(scope="web-app")

logger.info("User login successful", user_id=123, ip="192.168.1.1")
logger.error("User login failed", username="Bob")
```

Example output:

```json
{
  "severity": "INFO",
  "scope": "web-app",
  "message": "User login successful",
  "timestamp": "2026-01-21T19:55:00.000000Z",
  "fields": {
    "user_id": 123,
    "ip": "192.168.1.1"
  }
}
```

```json
{
  "severity": "ERROR",
  "scope": "web-app",
  "message": "User login failed",
  "timestamp": "2026-01-21T19:55:01.000000Z",
  "fields": {
    "username": "Bob"
  },
  "module": "views",
  "function": "login",
  "line": 42
}
```

## Core Features

### Logging Methods

`ConvLogPy` exposes the standard logging methods:

```python
logger.debug("Debug message", foo="bar")
logger.info("Info message")
logger.warning("Warning message", context="auth")
logger.error("Error message", error_code=500)
logger.critical("Critical issue", system="payments")
logger.exception("Exception occurred", traceback=exc_info)
```

All keyword arguments passed to these methods are added under the `fields` key.

### Scope

You can set a default **scope** at initialization:

```python
logger = ConvLogPy(scope="billing-service")
```

You can also override it per log call:

```python
logger.info("Processing payment", scope="payment-worker", order_id=42)
```

### Console vs File Logging

By default, logs go to stdout. You can disable console output:

```python
# Disable console logging
logger = ConvLogPy(scope="service", console=False)

# Add file handlers only
logger.add_file_handler("app.log")
```

## File Logging

### Basic File Handler

```python
logger = ConvLogPy(scope="my-app", console=False)

# Add a simple file handler
logger.add_file_handler("logs/app.log")

# Add error-only logs to separate file
logger.add_file_handler("logs/error.log", level=40)  # 40 = logging.ERROR

# Log messages
logger.info("Application started")
logger.error("Something went wrong", error_code=500)
```

## Debug

### Debug function local variables and arguments

```python
log = convlogpy.ConvLogPy(scope="function.admin")
@log.debug_vars(['t', 'x', 's']) # Enter only variable you want to retrieve value after function execution, usefull to debugging without modify your function
def my_function(age=10):
    x = None
    t = 1
    age += 10
    s = "je suis deja la"
```

