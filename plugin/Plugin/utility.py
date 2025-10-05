import json
import logging
import mimetypes
import os
from datetime import datetime
from pathlib import Path

from qgis.PyQt.QtWidgets import QMessageBox

# =============================================================================
# MESSAGE DISPLAY UTILITIES
# =============================================================================


def display_user_message(window, title, message):
    """Display an informational message to the user"""
    msg_box = QMessageBox(window)
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()


def display_error_message(window, title, message):
    """Display an error message to the user"""
    msg_box = QMessageBox(window)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()


# =============================================================================
# MIME TYPE UTILITIES
# =============================================================================


def _load_custom_mimetypes():
    """Load custom MIME type mappings from JSON file"""
    current_dir = Path(__file__).parent
    json_file_path = current_dir / "mimetypes.json"
    try:
        if os.path.exists(json_file_path):
            with open(json_file_path, "r") as f:
                return json.load(f)
        else:
            return {}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading custom MIME types: {e}")
        return {}


def get_mimetype(file_path):
    """
    Get MIME type using built-in mimetypes first, then custom mappings

    Args:
        file_path: Path to file or just filename with extension

    Returns:
        str: MIME type or 'application/octet-stream' as final fallback
    """
    # Try built-in mimetypes first
    mimetype, _ = mimetypes.guess_type(file_path)
    if mimetype:
        return mimetype

    # If no built-in match, try custom mappings
    custom_mimetypes = _load_custom_mimetypes()
    if custom_mimetypes:
        # Get file extension without the dot
        extension = Path(file_path).suffix.lower().lstrip(".")
        if extension in custom_mimetypes:
            return custom_mimetypes[extension]

    # Final fallback
    return "application/octet-stream"


# =============================================================================
# LOGGING UTILITIES
# =============================================================================


class MemoryHandler(logging.Handler):
    """Custom handler that stores log records in memory"""

    def __init__(self):
        super().__init__()
        self.log_entries = []

    def emit(self, record):
        """Store the formatted log record"""
        log_entry = self.format(record)
        self.log_entries.append(log_entry)

    def get_logs(self):
        """Return all stored log entries"""
        return self.log_entries

    def clear_logs(self):
        """Clear all stored log entries"""
        self.log_entries.clear()


class Logger:
    """Singleton logger class for QGIS RO-Crate operations"""

    _instance = None
    _logger = None
    _log_entries = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        """Set up the logger with memory handler"""
        self._logger = logging.getLogger("qgis_rocrate")
        self._logger.setLevel(logging.DEBUG)

        self._logger.handlers.clear()

        # Create custom handler that stores logs in memory
        self.memory_handler = MemoryHandler()
        self.memory_handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        self.memory_handler.setFormatter(formatter)

        # Add handler to logger
        self._logger.addHandler(self.memory_handler)

    def get_logger(self, name=None):
        """Get a logger instance"""
        if name:
            return logging.getLogger(f"qgis_rocrate.{name}")
        return self._logger

    def write_logs_to_file(self, export_path, project_title):
        """Write all accumulated logs to file"""
        try:
            log_filename = f"{project_title}_export_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            log_file_path = os.path.join(export_path, log_filename)

            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write(f"RO-Crate Export Log for: {project_title}\n")
                f.write(f"Export Date: {datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n\n")

                for log_entry in self.memory_handler.get_logs():
                    f.write(log_entry + "\n")

            return log_file_path

        except Exception as e:
            display_error_message(None, "Log Error", f"Failed to write log file: {e}")
            return None

    def clear_logs(self):
        """Clear accumulated logs"""
        self.memory_handler.clear_logs()


def get_logger(name=None):
    """
    Convenience function to get logger instance

    Args:
        name: Optional name for the logger

    Returns:
        Logger instance
    """
    return Logger().get_logger(name)
