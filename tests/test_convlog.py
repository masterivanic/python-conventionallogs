import json
import tempfile
import unittest
import io
from pathlib import Path
from unittest.mock import patch
from convlogpy.convlogpy import ConvLogPy


class TestConvLogPy(unittest.TestCase):
    
    def setUp(self):
        if ConvLogPy in ConvLogPy._instances:
            del ConvLogPy._instances[ConvLogPy]
    
    def tearDown(self):
        if ConvLogPy in ConvLogPy._instances:
            del ConvLogPy._instances[ConvLogPy]
    
    def test_basic_logging(self):
        logger = ConvLogPy(scope="test")
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            logger._logger.addHandler(logger)
            logger.info("Test message", test_id=123)
            
            output = mock_stdout.getvalue()
            
            log_data = json.loads(output.strip())
            self.assertEqual(log_data["severity"], "INFO")
            self.assertEqual(log_data["scope"], "test")
            self.assertEqual(log_data["message"], "Test message")
            self.assertEqual(log_data["fields"]["test_id"], 123)
    
    def test_debug_logging(self):
        logger = ConvLogPy(scope="test-debug")
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            logger._logger.addHandler(logger)
            
            logger.debug("Debug message", debug_info="test")
            
            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())
            
            self.assertEqual(log_data["severity"], "DEBUG")
            self.assertEqual(log_data["message"], "Debug message")
    
    def test_warning_logging(self):
        logger = ConvLogPy(scope="test-warning")
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            logger._logger.addHandler(logger)
            
            logger.warning("Warning message", context="test")
            
            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())
            
            self.assertEqual(log_data["severity"], "WARNING")
            self.assertEqual(log_data["message"], "Warning message")
    
    def test_error_logging(self):
        logger = ConvLogPy(scope="error-test")
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            logger._logger.addHandler(logger)
            logger.error("An error occurred", error_type="test")
            
            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())
            
            self.assertEqual(log_data["severity"], "ERROR")
            self.assertEqual(log_data["message"], "An error occurred")
            self.assertIn("fields", log_data)
            self.assertEqual(log_data["fields"]["error_type"], "test")
            # Error logs should include module/function/line info
            self.assertIn("module", log_data["fields"])
            self.assertIn("function", log_data["fields"])
            self.assertIn("line", log_data["fields"])
    
    def test_critical_logging(self):
        logger = ConvLogPy(scope="test-critical")
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            logger._logger.addHandler(logger)
            
            logger.critical("Critical message", system="test")
            
            output = mock_stdout.getvalue()
            log_data = json.loads(output.strip())
            
            self.assertEqual(log_data["severity"], "CRITICAL")
            self.assertEqual(log_data["message"], "Critical message")
    
    def test_file_handler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = ConvLogPy(scope="file-test", console=False)
            
            logger.add_file_handler(log_file)
            logger.info("File test message", test="file")
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            self.assertGreater(len(lines), 0)
            log_data = json.loads(lines[0].strip())
            self.assertEqual(log_data["message"], "File test message")
            self.assertEqual(log_data["fields"]["test"], "file")
    
   
    
    def test_rotating_file_handler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "rotating.log"
            logger = ConvLogPy(scope="rotating-test", console=False)
        
            logger.add_rotating_file_handler(
                log_file,
                max_bytes=100,  
                backup_count=2
            )
            
            for i in range(10):
                logger.info(f"Message {i}", index=i)
            
            base_files = list(Path(tmpdir).glob("rotating.log*"))
            self.assertGreater(len(base_files), 1)
    
    
    def test_debug_vars_decorator(self):
        logger = ConvLogPy(scope="debug-test")
        
        @logger.debug_vars(['result', 'intermediate'])
        def test_function(x, y=2):
            intermediate = x + y
            result = intermediate * 2
            return result
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            logger._logger.addHandler(logger)
            
            test_function(5, y=3)
            
            output = mock_stdout.getvalue()
            lines = [json.loads(line.strip()) for line in output.strip().split('\n') if line]
            
            self.assertGreaterEqual(len(lines), 2)
            
            arg_log = next((line for line in lines if "Arguments of function" in line["message"]), None)
            self.assertIsNotNone(arg_log)
            self.assertEqual(arg_log["fields"]["x"], 5)
            self.assertEqual(arg_log["fields"]["y"], 3)
            
            var_log = next((line for line in lines if "Variables of function" in line["message"]), None)
            self.assertIsNotNone(var_log)
            self.assertIn("result", var_log["fields"])
            self.assertIn("intermediate", var_log["fields"])