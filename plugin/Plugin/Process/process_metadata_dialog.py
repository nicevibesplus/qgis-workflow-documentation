# -*- coding: utf-8 -*-
"""
Process Metadata Dialog - Dialog for documenting processing step metadata
"""

import json

from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtGui import QFont
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QVBoxLayout,
)


class ProcessMetadataDialog(QDialog):
    """Dialog for documenting processing step metadata"""

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, parent=None, process=None):
        """Initialize the Process Metadata Dialog.
        
        :param parent: Parent widget
        :type parent: QWidget
        :param process: Process object to document
        :type process: Process
        """
        super().__init__(parent)
        self.process = process
        self.setup_ui()
        self._setup_logic()

    # ============================================================================
    # UI SETUP
    # ============================================================================

    def setup_ui(self):
        """Setup the user interface"""
        algorithm_display = getattr(self.process, "algorithm_id", "Unknown")

        self.setWindowTitle("Process Metadata Documentation")
        self.setMinimumSize(700, 800)
        self.resize(700, 800)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Process info label
        self.process_info_label = QLabel(
            f'Document metadata for process "{algorithm_display}"'
        )
        self.process_info_label.setWordWrap(True)
        self.process_info_label.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignTop
        )
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.process_info_label.setFont(font)
        self.process_info_label.setStyleSheet("QLabel { color: #2c3e50; }")
        main_layout.addWidget(self.process_info_label)

        # Basic Information Group (editable)
        basic_info_group = QGroupBox("Basic Information")
        basic_info_layout = QFormLayout()
        basic_info_layout.setSpacing(12)
        basic_info_layout.setContentsMargins(15, 15, 15, 15)

        # Name
        self.name_lineedit = QLineEdit()
        self.name_lineedit.setPlaceholderText(
            "Enter a descriptive name for this process..."
        )
        self.name_lineedit.setToolTip(
            "Provide a human-readable name for this processing step"
        )
        basic_info_layout.addRow("Name:", self.name_lineedit)

        # Description
        self.description_textedit = QTextEdit()
        self.description_textedit.setMaximumHeight(80)
        self.description_textedit.setPlaceholderText(
            "Enter a description of what this process does..."
        )
        self.description_textedit.setToolTip(
            "Describe the purpose and function of this processing step"
        )
        basic_info_layout.addRow("Description:", self.description_textedit)

        basic_info_group.setLayout(basic_info_layout)
        main_layout.addWidget(basic_info_group)

        # Technical Information Group (read-only)
        tech_info_group = QGroupBox("Technical Information")
        tech_info_layout = QFormLayout()
        tech_info_layout.setSpacing(12)
        tech_info_layout.setContentsMargins(15, 15, 15, 15)

        # Algorithm ID (read-only)
        self.algorithm_id_lineedit = QLineEdit()
        self.algorithm_id_lineedit.setReadOnly(True)
        self.algorithm_id_lineedit.setStyleSheet(
            "QLineEdit:read-only { background-color: #f8f9fa; color: #6c757d; }"
        )
        tech_info_layout.addRow("Algorithm ID:", self.algorithm_id_lineedit)

        # Timestamp (read-only)
        self.timestamp_lineedit = QLineEdit()
        self.timestamp_lineedit.setReadOnly(True)
        self.timestamp_lineedit.setStyleSheet(
            "QLineEdit:read-only { background-color: #f8f9fa; color: #6c757d; }"
        )
        tech_info_layout.addRow("Timestamp:", self.timestamp_lineedit)

        # Process ID (read-only)
        self.process_id_lineedit = QLineEdit()
        self.process_id_lineedit.setReadOnly(True)
        self.process_id_lineedit.setStyleSheet(
            "QLineEdit:read-only { background-color: #f8f9fa; color: #6c757d; }"
        )
        tech_info_layout.addRow("Process ID:", self.process_id_lineedit)

        tech_info_group.setLayout(tech_info_layout)
        main_layout.addWidget(tech_info_group)

        # Parameters Group (read-only)
        parameters_group = QGroupBox("Parameters")
        parameters_layout = QVBoxLayout()
        parameters_layout.setSpacing(12)
        parameters_layout.setContentsMargins(15, 15, 15, 15)

        self.parameters_textedit = QTextEdit()
        self.parameters_textedit.setMaximumHeight(120)
        self.parameters_textedit.setReadOnly(True)
        self.parameters_textedit.setStyleSheet(
            "QTextEdit:read-only { background-color: #f8f9fa; color: #6c757d; font-family: monospace; }"
        )
        parameters_layout.addWidget(self.parameters_textedit)

        parameters_group.setLayout(parameters_layout)
        main_layout.addWidget(parameters_group)

        # Results Group (read-only)
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        results_layout.setSpacing(12)
        results_layout.setContentsMargins(15, 15, 15, 15)

        self.results_textedit = QTextEdit()
        self.results_textedit.setMaximumHeight(120)
        self.results_textedit.setReadOnly(True)
        self.results_textedit.setStyleSheet(
            "QTextEdit:read-only { background-color: #f8f9fa; color: #6c757d; font-family: monospace; }"
        )
        results_layout.addWidget(self.results_textedit)

        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

        # Log Group (read-only)
        log_group = QGroupBox("Process Log")
        log_layout = QVBoxLayout()
        log_layout.setSpacing(12)
        log_layout.setContentsMargins(15, 15, 15, 15)

        self.log_textedit = QTextEdit()
        self.log_textedit.setMaximumHeight(120)
        self.log_textedit.setReadOnly(True)
        self.log_textedit.setStyleSheet(
            "QTextEdit:read-only { background-color: #f8f9fa; color: #6c757d; font-family: monospace; }"
        )
        log_layout.addWidget(self.log_textedit)

        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Spacer
        spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(spacer)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Horizontal spacer
        button_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout.addItem(button_spacer)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumSize(80, 30)
        button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("Save Metadata")
        self.save_button.setMinimumSize(120, 30)
        self.save_button.setDefault(True)
        self.save_button.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """
        )
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def _setup_logic(self):
        """Setup logic and connections"""
        # Initialize fields with process data
        self._populate_fields()

        # Setup validation timer
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._perform_real_time_validation)

        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._validate_and_accept)

        # Field change connections for real-time validation
        self.name_lineedit.textChanged.connect(self._on_text_changed)
        self.description_textedit.textChanged.connect(self._on_text_changed)

        # Initial validation
        self._perform_real_time_validation()

    def _populate_fields(self):
        """Populate fields with process data"""
        # Editable fields
        if hasattr(self.process, "name") and self.process.name:
            self.name_lineedit.setText(self.process.name)
        if hasattr(self.process, "description") and self.process.description:
            self.description_textedit.setPlainText(self.process.description)

        # Technical information (read-only)
        algorithm_id = getattr(self.process, "algorithm_id", "Unknown")
        self.algorithm_id_lineedit.setText(str(algorithm_id))

        timestamp = getattr(self.process, "timestamp", "Unknown")
        self.timestamp_lineedit.setText(str(timestamp))

        process_id = getattr(self.process, "id", "Unknown")
        self.process_id_lineedit.setText(str(process_id))

        # Parameters (read-only, formatted JSON)
        parameters = getattr(self.process, "parameters", {})
        try:
            formatted_parameters = json.dumps(parameters, indent=2, sort_keys=True)
            self.parameters_textedit.setPlainText(formatted_parameters)
        except Exception:
            self.parameters_textedit.setPlainText(str(parameters))

        # Results (read-only, formatted JSON)
        results = getattr(self.process, "results", {})
        try:
            formatted_results = json.dumps(results, indent=2, sort_keys=True)
            self.results_textedit.setPlainText(formatted_results)
        except Exception:
            self.results_textedit.setPlainText(str(results))

        # Log (read-only)
        log = getattr(self.process, "log", "No log available")
        self.log_textedit.setHtml(str(log))

        # Set initial focus
        self.name_lineedit.setFocus()

    # ============================================================================
    # VALIDATION
    # ============================================================================

    def _on_text_changed(self):
        """Handle text changes with delayed validation"""
        self.validation_timer.stop()
        self.validation_timer.start(300)  # 300ms delay

    def _perform_real_time_validation(self):
        """Perform real-time validation of fields"""
        name_valid = self._validate_name_field()
        description_valid = self._validate_description_field()

        all_valid = name_valid and description_valid
        self.save_button.setEnabled(all_valid)

    def _validate_name_field(self):
        """Validate name field.
        
        :return: True if valid, False otherwise
        :rtype: bool
        """
        text = self.name_lineedit.text().strip()
        if len(text) >= 3:
            self._apply_validation_styles(self.name_lineedit, "valid")
            return True
        elif len(text) == 0:
            self._apply_validation_styles(self.name_lineedit, "neutral")
            return False
        else:
            self._apply_validation_styles(self.name_lineedit, "invalid")
            return False

    def _validate_description_field(self):
        """Validate description field.
        
        :return: True if valid, False otherwise
        :rtype: bool
        """
        text = self.description_textedit.toPlainText().strip()
        if len(text) >= 10:
            self._apply_validation_styles(self.description_textedit, "valid")
            return True
        elif len(text) == 0:
            self._apply_validation_styles(self.description_textedit, "neutral")
            return False
        else:
            self._apply_validation_styles(self.description_textedit, "invalid")
            return False

    def _apply_validation_styles(self, widget, state):
        """Apply validation styles to a widget.
        
        :param widget: Widget to apply styles to
        :type widget: QWidget
        :param state: Validation state ('valid', 'invalid', or 'neutral')
        :type state: str
        """
        if state == "invalid":
            widget.setStyleSheet("border: 2px solid #e74c3c; border-radius: 3px;")
        elif state == "valid":
            widget.setStyleSheet("border: 2px solid #27ae60; border-radius: 3px;")
        else:  # neutral
            widget.setStyleSheet("")

    def _validate_and_accept(self):
        """Final validation before accepting the dialog"""
        name_text = self.name_lineedit.text().strip()
        description_text = self.description_textedit.toPlainText().strip()

        # Validate required fields
        if not name_text or len(name_text) < 3:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Name is required and must be at least 3 characters long for the process.",
            )
            self.name_lineedit.setFocus()
            return

        if not description_text or len(description_text) < 10:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Description is required and must be at least 10 characters long for the process.",
            )
            self.description_textedit.setFocus()
            return

        # Update process properties
        self.process.set_name_description(name_text, description_text)

        self.accept()

    # ============================================================================
    # PUBLIC INTERFACE
    # ============================================================================

    def get_metadata(self):
        """Get the process metadata as a dictionary.
        
        :return: Dictionary containing process metadata
        :rtype: dict
        """
        timestamp_str = str(self.process.timestamp)
        if hasattr(self.process.timestamp, "toString"):
            timestamp_str = self.process.timestamp.toString("yyyy-MM-dd hh:mm:ss")

        return {
            "name": self.name_lineedit.text().strip(),
            "description": self.description_textedit.toPlainText().strip(),
            "algorithm_id": getattr(self.process, "algorithm_id", "Unknown"),
            "timestamp": timestamp_str,
            "process_id": getattr(self.process, "id", "Unknown"),
        }