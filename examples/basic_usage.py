import logging
from convlogpy.convlogpy import ConvLogPy


def main():
    logger = ConvLogPy(scope="example-app")

    logger.debug("Debug message", debug_info="additional debug data")
    logger.info("Application started", version="1.0.0")
    logger.warning("Resource usage high", cpu_percent=85, memory_mb=2048)
    logger.error("Failed to connect", endpoint="api.example.com", retries=3)

    print("\n" + "=" * 40 + "\n")

    file_logger = ConvLogPy(scope="file-example", console=False)
    file_logger.add_file_handler("example.log")
    file_logger.add_file_handler("errors.log", level=logging.ERROR)

    file_logger.info("This goes to example.log")
    file_logger.error("This goes to both example.log and errors.log")

    print("Logs written to example.log and errors.log")

    rotating_logger = ConvLogPy(scope="rotating-example", console=False)

    rotating_logger.add_rotating_file_handler(
        "rotating.log", max_bytes=1024, backup_count=3
    )

    for i in range(10):
        rotating_logger.info(f"Log message {i}", iteration=i)

    print("Rotating logs created: rotating.log, rotating.log.1, etc.")

    print("\n" + "=" * 40 + "\n")

    # Example 4: Function debugging
    print("Example 4: Function Debugging")
    print("=" * 40)

    debug_logger = ConvLogPy(scope="debug-example", console=True)

    @debug_logger.debug_vars(["result", "processed_data"])
    def process_data(data, multiplier=2):
        """Example function with debug variables."""
        processed_data = [x * multiplier for x in data]
        result = sum(processed_data)
        return result

    # This will log function arguments and specified variables
    data = [1, 2, 3, 4, 5]
    total = process_data(data, multiplier=3)
    print(f"Result: {total}")

    print("\n" + "=" * 40 + "\n")

    # Example 5: Error with traceback
    print("Example 5: Error with Context")
    print("=" * 40)

    error_logger = ConvLogPy(scope="error-example")

    try:
        10 / 0
    except ZeroDivisionError:
        error_logger.exception(
            "Division by zero occurred", dividend=10, divisor=0, operation="division"
        )


if __name__ == "__main__":
    main()
