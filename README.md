# ConvLogPy

`ConvLogPy` is a lightweight JSON logger built on top of Python’s standard `logging` module. It outputs structured logs to `stdout`, making them easy to parse, search, and aggregate in modern log management systems.

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


## Usage

### Basic example

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

### Logging methods

`ConvLogPy` exposes the standard logging methods:

```python
logger.debug("Debug message", foo="bar")
logger.info("Info message")
logger.warning("Warning message", context="auth")
logger.error("Error message", error_code=500)
logger.critical("Critical issue", system="payments")
```

All keyword arguments passed to these methods are added under the `fields` key.

### Scope

You can set a default **scope** at initialization:

```python
logger = PyLogger(scope="billing-service")
```

You can also override it per log call:

```python
logger.info("Processing payment", scope="payment-worker", order_id=42)
```

## How it works

- `ConvLogPy` subclasses `logging.Handler` and uses a metaclass-based singleton to ensure only one instance per process.  
- `emit` formats `logging.LogRecord` into a JSON-serializable dictionary and writes it to `stdout`.  
- For `ERROR` level logs, additional metadata (`module`, `function`, `line`) is injected for easier debugging.

## Running the example

The module includes a simple usage example:

```bash
python convlogpy.py
```

This will create a logger with `scope="my-scope"` and emit an `INFO` and an `ERROR` log entry.


