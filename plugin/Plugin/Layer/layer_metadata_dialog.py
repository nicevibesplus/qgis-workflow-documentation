import re

from qgis.PyQt.QtCore import QDate, Qt, QTimer, pyqtSignal
from qgis.PyQt.QtGui import QFont
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QVBoxLayout,
)

from ..utility import display_error_message


class LayerMetadataDialog(QDialog):
    """Dialog for documenting layer metadata and external source information.

    This dialog allows users to add descriptions, mark layers as external sources,
    and document external source information including title, URL, date, and comments.
    Provides real-time validation and styled feedback for user input.
    """

    # Signal emitted when layer metadata is successfully saved
    metadata_documented = pyqtSignal(dict)

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, parent=None, layer=None):
        """Initialize the LayerMetadataDialog.

        :param parent: Parent widget
        :type parent: QWidget or None
        :param layer: Layer object to document metadata for
        :type layer: Layer or None
        """
        super().__init__(parent)
        self.layer = layer
        self.setup_ui()
        self.setup_logic()

    def setup_ui(self):
        """Setup the user interface components and layout."""
        self.setWindowTitle("Layer Metadata Documentation")
        self.setMinimumSize(650, 700)
        self.resize(650, 700)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Add UI components
        self._create_header_section(main_layout)
        self._create_basic_info_section(main_layout)
        self._create_layer_properties_section(main_layout)
        self._create_technical_info_section(main_layout)
        self._create_external_source_section(main_layout)
        self._create_button_section(main_layout)

        self.setLayout(main_layout)

    def setup_logic(self):
        """Setup logic, connections, and initialize field validation."""
        # Initialize fields with layer data
        self.populate_fields()

        # Setup validation timer
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.perform_real_time_validation)

        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.validate_and_accept)
        self.external_checkbox.toggled.connect(self.on_external_changed)

        # Field change connections for real-time validation
        self.description_textedit.textChanged.connect(self.on_text_changed)
        self.source_title_lineedit.textChanged.connect(self.on_text_changed)
        self.source_url_lineedit.textChanged.connect(self.on_text_changed)
        self.source_date_dateedit.dateChanged.connect(self.perform_real_time_validation)
        self.source_comment_textedit.textChanged.connect(self.on_text_changed)

        # Initial validation
        self.perform_real_time_validation()

    # ============================================================================
    # UI CREATION METHODS
    # ============================================================================

    def _create_header_section(self, main_layout):
        """Create the header section with layer information.

        :param main_layout: Main layout to add the header to
        :type main_layout: QVBoxLayout
        """
        layer_name = getattr(self.layer, "name", "Unnamed Layer")

        self.layer_info_label = QLabel(f'Document metadata for layer "{layer_name}"')
        self.layer_info_label.setWordWrap(True)
        self.layer_info_label.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignTop)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.layer_info_label.setFont(font)
        self.layer_info_label.setStyleSheet("QLabel { color: #2c3e50; }")
        main_layout.addWidget(self.layer_info_label)

    def _create_basic_info_section(self, main_layout):
        """Create the basic information section.

        :param main_layout: Main layout to add the section to
        :type main_layout: QVBoxLayout
        """
        basic_info_group = QGroupBox("Basic Information")
        basic_info_layout = QFormLayout()
        basic_info_layout.setSpacing(12)
        basic_info_layout.setContentsMargins(15, 15, 15, 15)

        # Layer Name
        self.layer_name_lineedit = QLineEdit()
        self.layer_name_lineedit.setReadOnly(True)
        self.layer_name_lineedit.setStyleSheet(
            "QLineEdit:read-only { background-color: #f8f9fa; color: #6c757d; }"
        )
        basic_info_layout.addRow("Layer Name:", self.layer_name_lineedit)

        # Description
        self.description_textedit = QTextEdit()
        self.description_textedit.setMaximumHeight(80)
        self.description_textedit.setPlaceholderText(
            "Enter a description of this layer's content and purpose..."
        )
        self.description_textedit.setToolTip(
            "Provide a clear description of what this layer contains and its intended use"
        )
        basic_info_layout.addRow("Description:", self.description_textedit)

        basic_info_group.setLayout(basic_info_layout)
        main_layout.addWidget(basic_info_group)

    def _create_layer_properties_section(self, main_layout):
        """Create the layer properties section.

        :param main_layout: Main layout to add the section to
        :type main_layout: QVBoxLayout
        """
        layer_props_group = QGroupBox("Layer Properties")
        layer_props_layout = QFormLayout()
        layer_props_layout.setSpacing(12)
        layer_props_layout.setContentsMargins(15, 15, 15, 15)

        # Layer Visible (read-only)
        self.layer_visible_lineedit = QLineEdit()
        self.layer_visible_lineedit.setReadOnly(True)
        self.layer_visible_lineedit.setStyleSheet(
            "QLineEdit:read-only { background-color: #f8f9fa; color: #6c757d; }"
        )
        self.layer_visible_lineedit.setToolTip(
            "Shows whether this layer is currently visible in QGIS"
        )
        layer_props_layout.addRow("Layer Visible:", self.layer_visible_lineedit)

        # External Source checkbox
        self.external_checkbox = QCheckBox(
            "This layer comes from an external data source"
        )
        self.external_checkbox.setToolTip(
            "Check if this layer was downloaded or comes from an external source"
        )
        layer_props_layout.addRow("External Source:", self.external_checkbox)

        layer_props_group.setLayout(layer_props_layout)
        main_layout.addWidget(layer_props_group)

    def _create_technical_info_section(self, main_layout):
        """Create the technical information section.

        :param main_layout: Main layout to add the section to
        :type main_layout: QVBoxLayout
        """
        tech_info_group = QGroupBox("Technical Information")
        tech_info_layout = QFormLayout()
        tech_info_layout.setSpacing(12)
        tech_info_layout.setContentsMargins(15, 15, 15, 15)

        # Layer Type (read-only)
        self.tech_layer_type_lineedit = QLineEdit()
        self.tech_layer_type_lineedit.setReadOnly(True)
        self.tech_layer_type_lineedit.setStyleSheet(
            "QLineEdit:read-only { background-color: #f8f9fa; color: #6c757d; }"
        )
        tech_info_layout.addRow("Layer Type:", self.tech_layer_type_lineedit)

        # Source (read-only)
        self.source_lineedit = QLineEdit()
        self.source_lineedit.setReadOnly(True)
        self.source_lineedit.setStyleSheet(
            "QLineEdit:read-only { background-color: #f8f9fa; color: #6c757d; }"
        )
        tech_info_layout.addRow("Data Source:", self.source_lineedit)

        # Clean Name (read-only)
        self.clean_name_lineedit = QLineEdit()
        self.clean_name_lineedit.setReadOnly(True)
        self.clean_name_lineedit.setStyleSheet(
            "QLineEdit:read-only { background-color: #f8f9fa; color: #6c757d; }"
        )
        tech_info_layout.addRow("Clean Name:", self.clean_name_lineedit)

        tech_info_group.setLayout(tech_info_layout)
        main_layout.addWidget(tech_info_group)

    def _create_external_source_section(self, main_layout):
        """Create the external source information section.

        :param main_layout: Main layout to add the section to
        :type main_layout: QVBoxLayout
        """
        self.source_info_group = QGroupBox("External Source Information")
        self.source_info_group.setVisible(False)
        source_info_layout = QFormLayout()
        source_info_layout.setSpacing(12)
        source_info_layout.setContentsMargins(15, 15, 15, 15)

        # Source Title
        self.source_title_lineedit = QLineEdit()
        self.source_title_lineedit.setPlaceholderText(
            "Name or title of the data source"
        )
        self.source_title_lineedit.setToolTip(
            "Enter the official name or title of the data source"
        )
        source_info_layout.addRow("Source Title:", self.source_title_lineedit)

        # Source URL
        self.source_url_lineedit = QLineEdit()
        self.source_url_lineedit.setPlaceholderText("https://example.com/data-source")
        self.source_url_lineedit.setToolTip(
            "Enter the URL where this data was obtained"
        )
        source_info_layout.addRow("Source URL:", self.source_url_lineedit)

        # Source Date
        self.source_date_dateedit = QDateEdit()
        self.source_date_dateedit.setCalendarPopup(True)
        self.source_date_dateedit.setDisplayFormat("yyyy-MM-dd")
        self.source_date_dateedit.setDate(QDate.currentDate())
        self.source_date_dateedit.setToolTip(
            "Select the date when this data was downloaded or last updated"
        )
        source_info_layout.addRow("Source Date:", self.source_date_dateedit)

        # Source Comment
        self.source_comment_textedit = QTextEdit()
        self.source_comment_textedit.setMaximumHeight(80)
        self.source_comment_textedit.setPlaceholderText(
            "Optional: Additional notes about the data source, processing, or quality..."
        )
        self.source_comment_textedit.setToolTip(
            "Add any relevant comments about the data source, quality, or processing notes"
        )
        source_info_layout.addRow("Source Comment:", self.source_comment_textedit)

        self.source_info_group.setLayout(source_info_layout)
        main_layout.addWidget(self.source_info_group)

    def _create_button_section(self, main_layout):
        """Create the button section.

        :param main_layout: Main layout to add the section to
        :type main_layout: QVBoxLayout
        """
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

    # ============================================================================
    # DATA POPULATION METHODS
    # ============================================================================

    def populate_fields(self):
        """Populate dialog fields with existing layer data."""
        # Layer name
        layer_name = getattr(self.layer, "name", "")
        self.layer_name_lineedit.setText(layer_name)

        visibility_text = "Yes" if getattr(self.layer, "visible", False) else "No"
        self.layer_visible_lineedit.setText(visibility_text)

        # Technical information
        self.tech_layer_type_lineedit.setText(getattr(self.layer, "type", ""))
        self.source_lineedit.setText(str(getattr(self.layer, "source", "")))
        self.clean_name_lineedit.setText(getattr(self.layer, "clean_name", ""))

        self.external_checkbox.setChecked(getattr(self.layer, "external", False))

        # Description
        if hasattr(self.layer, "description") and self.layer.description:
            self.description_textedit.setPlainText(self.layer.description)

        # External source fields
        if hasattr(self.layer, "source_title") and self.layer.source_title:
            self.source_title_lineedit.setText(self.layer.source_title)
        if hasattr(self.layer, "source_url") and self.layer.source_url:
            self.source_url_lineedit.setText(self.layer.source_url)
        if hasattr(self.layer, "source_date") and self.layer.source_date:
            date = QDate.fromString(self.layer.source_date, "yyyy-MM-dd")
            if date.isValid():
                self.source_date_dateedit.setDate(date)
        if hasattr(self.layer, "source_comment") and self.layer.source_comment:
            self.source_comment_textedit.setPlainText(self.layer.source_comment)

        self.description_textedit.setFocus()

        # Update UI based on external state
        self.update_ui_based_on_external_state()

    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================

    def on_external_changed(self):
        """Handle external checkbox state changes."""
        self.update_ui_based_on_external_state()
        self.perform_real_time_validation()

    def on_text_changed(self):
        """Handle text field changes with delayed validation."""
        self.validation_timer.stop()
        self.validation_timer.start(300)  # 300ms delay

    # ============================================================================
    # UI STATE MANAGEMENT
    # ============================================================================

    def update_ui_based_on_external_state(self):
        """Update UI elements visibility based on external checkbox state."""
        is_external = self.external_checkbox.isChecked()
        self.source_info_group.setVisible(is_external)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    def perform_real_time_validation(self):
        """Perform real-time validation of all form fields."""
        description_valid = self.validate_description_field()
        name_valid = True

        # If external is checked, validate external source fields
        is_external = self.external_checkbox.isChecked()
        if is_external:
            source_title_valid = self.validate_source_title_field()
            source_url_valid = self.validate_source_url_field()
            all_valid = (
                description_valid
                and name_valid
                and source_title_valid
                and source_url_valid
            )
        else:
            all_valid = description_valid and name_valid

        self.save_button.setEnabled(all_valid)

    def validate_description_field(self):
        """Validate the description field.

        :return: True if description is valid, False otherwise
        :rtype: bool
        """
        text = self.description_textedit.toPlainText().strip()
        if len(text) >= 3:
            self.apply_validation_styles(self.description_textedit, "valid")
            return True
        elif len(text) == 0:
            self.apply_validation_styles(self.description_textedit, "neutral")
            return False
        else:
            self.apply_validation_styles(self.description_textedit, "invalid")
            return False

    def validate_source_title_field(self):
        """Validate the source title field.

        :return: True if source title is valid, False otherwise
        :rtype: bool
        """
        text = self.source_title_lineedit.text().strip()
        if len(text) >= 2:
            self.apply_validation_styles(self.source_title_lineedit, "valid")
            return True
        elif len(text) == 0:
            self.apply_validation_styles(self.source_title_lineedit, "neutral")
            return False
        else:
            self.apply_validation_styles(self.source_title_lineedit, "invalid")
            return False

    def validate_source_url_field(self):
        """Validate the source URL field (optional but must be valid if provided).

        :return: True if source URL is valid or empty, False if invalid format
        :rtype: bool
        """
        text = self.source_url_lineedit.text().strip()
        if len(text) == 0:
            # URL is optional
            self.apply_validation_styles(self.source_url_lineedit, "neutral")
            return True
        elif self.is_valid_url(text):
            self.apply_validation_styles(self.source_url_lineedit, "valid")
            return True
        else:
            self.apply_validation_styles(self.source_url_lineedit, "invalid")
            return False

    def apply_validation_styles(self, widget, state):
        """Apply visual validation styles to a widget.

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

    def is_valid_url(self, url):
        """Check if URL has a valid format.

        :param url: URL string to validate
        :type url: str
        :return: True if URL format is valid, False otherwise
        :rtype: bool
        """

        url_pattern = re.compile(
            r"^https?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        return url_pattern.match(url) is not None

    def validate_and_accept(self):
        """Perform final validation before accepting the dialog."""
        description_text = self.description_textedit.toPlainText().strip()

        # Validate required fields
        if not description_text or len(description_text) < 3:
            display_error_message(
                self,
                "Validation Error",
                "Description is required and must be at least 3 characters long for the layer.",
            )
            self.description_textedit.setFocus()
            return

        is_external = self.external_checkbox.isChecked()

        # Update layer properties
        self.layer.set_description(description_text)
        self.layer.set_external(is_external)

        # If external, validate and set external source properties
        if is_external:
            source_title_text = self.source_title_lineedit.text().strip()
            source_url_text = self.source_url_lineedit.text().strip()

            if not source_title_text or len(source_title_text) < 2:
                display_error_message(
                    self,
                    "Validation Error",
                    "Source title is required and must be at least 2 characters long.",
                )
                self.source_title_lineedit.setFocus()
                return

            # Validate URL if provided
            if source_url_text and not self.is_valid_url(source_url_text):
                display_error_message(
                    self,
                    "Validation Error",
                    "Please enter a valid URL starting with http:// or https://",
                )
                self.source_url_lineedit.setFocus()
                return

            # Set external source properties
            self.layer.set_external_source_properties(
                source_title_text,
                source_url_text or "",
                self.source_date_dateedit.date().toString(Qt.ISODate),
                self.source_comment_textedit.toPlainText().strip() or "",
            )

        self.accept()

    # ============================================================================
    # PUBLIC INTERFACE
    # ============================================================================

    def get_metadata(self):
        """Get the current layer metadata as a dictionary.

        :return: Dictionary containing all layer metadata
        :rtype: dict
        """
        metadata = {
            "description": self.description_textedit.toPlainText().strip(),
            "external": self.external_checkbox.isChecked(),
        }

        if metadata["external"]:
            metadata.update(
                {
                    "source_title": self.source_title_lineedit.text().strip(),
                    "source_url": self.source_url_lineedit.text().strip() or None,
                    "source_date": self.source_date_dateedit.date().toString(
                        Qt.ISODate
                    ),
                    "source_comment": self.source_comment_textedit.toPlainText().strip()
                    or None,
                }
            )

        return metadata
