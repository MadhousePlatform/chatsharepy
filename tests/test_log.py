"""Unit tests for logging"""

import unittest
from pathlib import Path
import tempfile
import shutil
import time
import threading
from loguru import logger


class TestLogging(unittest.TestCase):
    """Unit tests for logging"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        # Save original logger configuration
        cls.original_handlers = logger._core.handlers.copy() # pylint: disable=protected-access

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        # Restore original logger configuration
        logger._core.handlers = cls.original_handlers # pylint: disable=protected-access

    def setUp(self):
        # Create a temporary directory for test logs
        self.test_log_dir = tempfile.mkdtemp()
        self.log_file_path = Path(self.test_log_dir) / "log-{time:YYYY-MM-DD}.log"

        # Remove default logger and set up test configuration
        logger.remove()
        self.log_id = logger.add(
            str(self.log_file_path),
            format="{time:HH:mm:ss} {level} ## {file}::{function}::{line} ## {message}",
            level="INFO"
        )

    def tearDown(self):
        # Clean up: remove logger and temporary directory
        logger.remove(self.log_id)
        shutil.rmtree(self.test_log_dir)

    def test_log_file_creation(self):
        """Test that log file is created when logging"""
        test_message = "Test log message"
        logger.info(test_message)

        # Get the actual log file name (with current date)
        log_files = list(Path(self.test_log_dir).glob("*.log"))
        self.assertEqual(len(log_files), 1, "Expected exactly one log file")

        # Read the log file content
        with open(log_files[0], 'r', encoding="UTF-8") as f:
            log_content = f.read()

        self.assertIn(test_message, log_content)

    def test_log_levels(self):
        """Test different log levels"""
        logger.debug("Debug message")  # Shouldn't appear in log
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        log_files = list(Path(self.test_log_dir).glob("*.log"))
        with open(log_files[0], 'r', encoding="UTF-8") as f:
            log_content = f.read()

        self.assertNotIn("Debug message", log_content)  # Debug messages shouldn't be logged
        self.assertIn("Info message", log_content)
        self.assertIn("Warning message", log_content)
        self.assertIn("Error message", log_content)

    def test_log_format(self):
        """Test log message format"""
        test_message = "Format test message"
        logger.info(test_message)

        log_files = list(Path(self.test_log_dir).glob("*.log"))
        with open(log_files[0], 'r', encoding="UTF-8") as f:
            log_content = f.read().strip()

        # Check if the log entry contains required components
        regex = r'\d{2}:\d{2}:\d{2}\s+INFO\s+##\s+test_log\.py::test_log_format::\d+\s+##\s+'
        self.assertRegex(
            log_content,
            regex + test_message
        )

    def test_log_rotation(self):
        """Test log rotation at midnight"""
        # Add a logger with rotation
        logger.remove(self.log_id)
        self.log_id = logger.add(
            str(self.log_file_path),
            format="{time:HH:mm:ss} {level} ## {file}::{function}::{line} ## {message}",
            level="INFO",
            rotation="00:00"
        )

        logger.info("Test rotation message")

        log_files = list(Path(self.test_log_dir).glob("*.log"))
        self.assertGreaterEqual(len(log_files), 1)

    def test_concurrent_logging(self):
        """Test logging from multiple threads"""

        def log_messages():
            for i in range(5):
                logger.info(f"Thread message {i}")
                time.sleep(0.1)

        threads = [
            threading.Thread(target=log_messages)
            for _ in range(3)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        log_files = list(Path(self.test_log_dir).glob("*.log"))
        with open(log_files[0], 'r', encoding="UTF-8") as f:
            log_content = f.read()

        # Should have 15 messages (5 messages * 3 threads)
        message_count = sum(1 for line in log_content.splitlines())
        self.assertEqual(message_count, 15)


if __name__ == '__main__':
    unittest.main()
