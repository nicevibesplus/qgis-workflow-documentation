# -*- coding: utf-8 -*-
"""
Export Tab Widget - Handles RO-Crate export functionality with programmatic UI
"""

import json
import os
import re
import shutil
import tempfile
import time
import zipfile

from qgis.PyQt.QtCore import QSize, Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QFileDialog,
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
    QWidget,
)
from qgis.utils import Qgis
from rocrate.rocrate import ROCrate

from ..utility import Logger, display_error_message, get_logger


class ExportTab(QWidget):
    # Signals for export events
    export_started = pyqtSignal()
    export_completed = pyqtSignal(str)  # export_path
    export_failed = pyqtSignal(str)  # error_message

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, parent=None):
        """Initialize the Export tab widget.

        :param parent: Parent widget
        :type parent: QWidget
        """
        super(ExportTab, self).__init__(parent)
        self.logger = get_logger("ExportTab")
        self.parent = parent
        self.setup_ui()
        self._initialize_ui_components()
        self._setup_signal_connections()

    # ============================================================================
    # UI SETUP
    # ============================================================================

    def setup_ui(self):
        """Set up the user interface programmatically"""
        self.setObjectName("ExportTab")
        self.resize(800, 600)
        self.setWindowTitle("Export")

        # Main layout
        self.export_layout = QVBoxLayout(self)
        self.export_layout.setSpacing(12)
        self.export_layout.setContentsMargins(10, 10, 10, 10)

        # Instruction label
        self.instruction_label = QLabel(self)
        self.instruction_label.setText(
            "Configure your project metadata and select an "
            "export location for the RO-Crate package."
        )
        self.instruction_label.setWordWrap(True)
        self.export_layout.addWidget(self.instruction_label)

        # author group
        self.author_group = QGroupBox(self)
        self.author_group.setTitle("Author Information")

        self.author_layout = QFormLayout(self.author_group)
        self.author_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.author_layout.setHorizontalSpacing(8)
        self.author_layout.setVerticalSpacing(8)
        self.author_layout.setContentsMargins(10, 10, 10, 10)

        # Author field
        self.author_label = QLabel("Author:", self)
        self.author_LineEdit = QLineEdit(self)
        self.author_LineEdit.setPlaceholderText("Enter author name")
        self.author_LineEdit.setToolTip("Name of the author")
        self.author_layout.addRow(self.author_label, self.author_LineEdit)

        # ORCID field
        self.orcid_label = QLabel("ORCID:", self)
        self.orcid_LineEdit = QLineEdit(self)
        self.orcid_LineEdit.setPlaceholderText("0000-0000-0000-0000")
        self.orcid_LineEdit.setToolTip("Your ORCID identifier (optional)")
        self.author_layout.addRow(self.orcid_label, self.orcid_LineEdit)

        # affiliation field
        self.affiliation_label = QLabel("Affiliation:", self)
        self.affiliation_LineEdit = QLineEdit(self)
        self.affiliation_LineEdit.setPlaceholderText("Enter affiliation")
        self.affiliation_LineEdit.setToolTip("Affiliation of the author (optional)")
        self.author_layout.addRow(self.affiliation_label, self.affiliation_LineEdit)

        self.export_layout.addWidget(self.author_group)

        self.metadata_group = QGroupBox(self)
        self.metadata_group.setTitle("Project Metadata")

        self.metadata_layout = QFormLayout(self.metadata_group)
        self.metadata_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.metadata_layout.setHorizontalSpacing(8)
        self.metadata_layout.setVerticalSpacing(8)
        self.metadata_layout.setContentsMargins(10, 10, 10, 10)

        # License field
        self.license_label = QLabel("License:", self)
        self.license_ComboBox = QComboBox(self)
        self.license_ComboBox.setToolTip(
            "Select the license for your dataset (required)"
        )
        self.license_ComboBox.setMinimumSize(QSize(0, 24))
        self.metadata_layout.addRow(self.license_label, self.license_ComboBox)

        # Title field
        self.title_label = QLabel("Project Title:", self)
        self.title_LineEdit = QLineEdit(self)
        self.title_LineEdit.setPlaceholderText("Enter project title")
        self.title_LineEdit.setToolTip("Title for your QGIS project")
        self.metadata_layout.addRow(self.title_label, self.title_LineEdit)

        # Description field
        self.description_label = QLabel("Description:", self)
        self.description_label.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignTop
        )
        self.description_TextEdit = QTextEdit(self)
        self.description_TextEdit.setMaximumSize(QSize(16777215, 100))
        self.description_TextEdit.setPlaceholderText("Enter project description")
        self.description_TextEdit.setToolTip(
            "Description of your QGIS project and its contents"
        )
        self.metadata_layout.addRow(self.description_label, self.description_TextEdit)

        self.export_layout.addWidget(self.metadata_group)

        # Export settings group
        self.export_settings_group = QGroupBox(self)
        self.export_settings_group.setTitle("Export Settings")

        self.export_settings_layout = QVBoxLayout(self.export_settings_group)
        self.export_settings_layout.setSpacing(8)
        self.export_settings_layout.setContentsMargins(10, 10, 10, 10)

        # Export path layout
        self.export_path_layout = QHBoxLayout()
        self.export_path_layout.setSpacing(8)

        self.export_path_label = QLabel("Export Path:", self)
        self.export_path_label.setMinimumSize(QSize(80, 0))
        self.export_path_layout.addWidget(self.export_path_label)

        self.export_path_LineEdit = QLineEdit(self)
        self.export_path_LineEdit.setPlaceholderText("Select folder to save RO-Crate")
        self.export_path_LineEdit.setReadOnly(True)
        self.export_path_LineEdit.setToolTip(
            "Directory where the RO-Crate will be saved"
        )
        self.export_path_layout.addWidget(self.export_path_LineEdit)

        self.browse_PushButton = QPushButton("Browse...", self)
        self.browse_PushButton.setMaximumSize(QSize(100, 16777215))
        self.browse_PushButton.setToolTip("Select export directory")
        self.export_path_layout.addWidget(self.browse_PushButton)

        self.export_settings_layout.addLayout(self.export_path_layout)
        self.export_layout.addWidget(self.export_settings_group)

        # Vertical spacer
        self.vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        self.export_layout.addItem(self.vertical_spacer)

        # Export button layout
        self.export_button_layout = QHBoxLayout()
        self.export_button_layout.setSpacing(8)

        self.button_spacer_left = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        self.export_button_layout.addItem(self.button_spacer_left)

        self.export_PushButton = QPushButton("Export RO-Crate", self)
        self.export_PushButton.setMinimumSize(QSize(150, 35))
        self.export_PushButton.setToolTip("Export QGIS project as RO-Crate package")
        self.export_PushButton.setEnabled(False)
        self.export_button_layout.addWidget(self.export_PushButton)

        self.button_spacer_right = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        self.export_button_layout.addItem(self.button_spacer_right)

        self.export_layout.addLayout(self.export_button_layout)

    def _initialize_ui_components(self):
        """Initialize and configure UI components for export tab"""
        # Apply styling to the export button
        self.export_PushButton.setStyleSheet(
            """
            QPushButton {
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """
        )

        # Initialize license dropdown with common licenses
        self._populate_license_dropdown()

    def _populate_license_dropdown(self):
        """Populate the license dropdown with common license types"""
        licenses = [
            ("", "Select a license..."),  # Empty option to force selection
            ("CC0-1.0", "CC0 1.0 Universal (Public Domain)"),
            ("CC-BY-4.0", "Creative Commons Attribution 4.0 International"),
            (
                "CC-BY-SA-4.0",
                "Creative Commons Attribution-ShareAlike 4.0 International",
            ),
            (
                "CC-BY-NC-4.0",
                "Creative Commons Attribution-NonCommercial 4.0 International",
            ),
            (
                "CC-BY-NC-SA-4.0",
                "Creative Commons Attribution-NonCommercial-ShareAlike "
                "4.0 International",
            ),
            ("MIT", "MIT License"),
            ("Apache-2.0", "Apache License 2.0"),
            ("GPL-3.0", "GNU General Public License v3.0"),
            ("BSD-3-Clause", "BSD 3-Clause License"),
            ("ODbL-1.0", "Open Database License v1.0"),
            ("PDDL-1.0", "Public Domain Dedication and License v1.0"),
            ("other", "Other (specify in description)"),
        ]

        self.license_ComboBox.clear()
        for license_id, license_name in licenses:
            self.license_ComboBox.addItem(license_name, license_id)

    def _setup_signal_connections(self):
        """Connect all button signals and user interaction events"""
        # Browse button for file path selection
        self.browse_PushButton.clicked.connect(self.browse_export_path)

        # Export button
        self.export_PushButton.clicked.connect(self.export_rocrate)

        # Field validation connections
        self.title_LineEdit.textChanged.connect(self.validate_form)
        self.export_path_LineEdit.textChanged.connect(self.validate_form)
        self.license_ComboBox.currentTextChanged.connect(self.validate_form)

    # ============================================================================
    # VALIDATION
    # ============================================================================

    def validate_form(self):
        """Validate form fields and enable/disable export button"""
        title = self.title_LineEdit.text().strip()
        description = self.description_TextEdit.toPlainText().strip()
        export_path = self.export_path_LineEdit.text().strip()
        author = self.author_LineEdit.text().strip()
        license_id = self.license_ComboBox.currentData()

        # Enable export button only if required fields are filled
        is_valid = bool(
            title and description and export_path and author and license_id
        )
        self.export_PushButton.setEnabled(is_valid)

    def validate_orcid(self, orcid):
        """Validate ORCID format (if provided).

        :param orcid: ORCID identifier to validate
        :type orcid: str
        :return: True if valid or empty, False otherwise
        :rtype: bool
        """
        if not orcid:
            return True  # ORCID is optional

        # Basic ORCID format validation: 0000-0000-0000-000X
        pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$"
        return bool(re.match(pattern, orcid))

    # ============================================================================
    # UTILITY / HELPER METHODS
    # ============================================================================

    def browse_export_path(self):
        """Open file dialog to select export directory"""
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if export_dir:
            self.export_path_LineEdit.setText(export_dir)

    def get_export_metadata(self):
        """Get all export metadata from form fields.

        :return: Dictionary containing all export metadata
        :rtype: dict
        """
        return {
            "author": self.author_LineEdit.text().strip(),
            "orcid": self.orcid_LineEdit.text().strip(),
            "affiliation": self.affiliation_LineEdit.text().strip(),
            "license": self.license_ComboBox.currentData(),
            "license_name": self.license_ComboBox.currentText(),
            "title": self.title_LineEdit.text().strip(),
            "description": self.description_TextEdit.toPlainText().strip(),
            "export_path": self.export_path_LineEdit.text().strip(),
        }

    def get_license_url(self, license_id):
        """Get the URL for a given license identifier.

        :param license_id: License identifier
        :type license_id: str
        :return: URL for the license, or None if not found
        :rtype: str or None
        """
        license_urls = {
            "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
            "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
            "CC-BY-SA-4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
            "CC-BY-NC-4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
            "CC-BY-NC-SA-4.0": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
            "MIT": "https://opensource.org/licenses/MIT",
            "Apache-2.0": "https://www.apache.org/licenses/LICENSE-2.0",
            "GPL-3.0": "https://www.gnu.org/licenses/gpl-3.0.html",
            "BSD-3-Clause": "https://opensource.org/licenses/BSD-3-Clause",
            "ODbL-1.0": "https://opendatacommons.org/licenses/odbl/1-0/",
            "PDDL-1.0": "https://opendatacommons.org/licenses/pddl/1-0/",
        }
        return license_urls.get(license_id, None)

    def clear_form(self):
        """Clear all form fields"""
        self.orcid_LineEdit.clear()
        self.license_ComboBox.setCurrentIndex(0)  # Reset to "Select a license..."
        self.title_LineEdit.clear()
        self.description_TextEdit.clear()
        self.export_path_LineEdit.clear()
        self.validate_form()  # Update button state

    def set_default_values(self, title=None, description=None, license_id=None):
        """Set default values for form fields.

        :param title: Default title
        :type title: str or None
        :param description: Default description
        :type description: str or None
        :param license_id: Default license ID
        :type license_id: str or None
        """
        if title:
            self.title_LineEdit.setText(title)
        if description:
            self.description_TextEdit.setPlainText(description)
        if license_id:
            # Find the index of the license_id in the combobox
            index = self.license_ComboBox.findData(license_id)
            if index >= 0:
                self.license_ComboBox.setCurrentIndex(index)
        self.validate_form()  # Update button state

    def _fix_rocrate_context(self, export_file_path):
        """Fix RO-Crate context issues in the exported zip file.

        :param export_file_path: Path to the exported RO-Crate zip file
        :type export_file_path: str
        """
        # Extract metadata
        with zipfile.ZipFile(export_file_path, "r") as zf:
            with zf.open("ro-crate-metadata.json") as f:
                metadata = json.load(f)

        # Add custom context
        custom_context = {
            "layerVisible": "isAccessibleForFree",
            "layerCrs": "spatialCoverage",
            "layerType": "additionalType",
            "layerFeatureCount": "numberOfItems",
            "layerGeometryType": "additionalType",
            "sourceTitle": "name",
            "sourceURL": "url",
            "sourceDate": "dateReceived",
            "sourceComment": "comment",
            "qgisLog": "text",
            "qgisParameters": "text",
            "qgisProcessCommand": "code",
            "qgisPythonCommand": "code",
            "qgisResults": "text",
        }

        # Ensure @context is a list and append
        if isinstance(metadata["@context"], list):
            metadata["@context"].append(
                "https://w3id.org/ro/terms/workflow-run/context"
            )  # process run crate
            metadata["@context"].append(custom_context)
        else:
            metadata["@context"] = [metadata["@context"], custom_context]

        for item in metadata["@graph"]:
            if item.get("@id") == "./":
                item["conformsTo"] = {
                    "@id": "https://w3id.org/ro/wfrun/process/0.5"
                }
                break

        metadata["@graph"].append(
            {
                "@id": "https://w3id.org/ro/wfrun/process/0.5",
                "@type": ["CreativeWork", "Profile"],
                "name": "Process Run crate profile",
                "version": "0.5.0",
            }
        )

        # Write back to a temporary zip
        fd, tmp_zip_path = tempfile.mkstemp(suffix=".zip")
        os.close(fd)

        with (
            zipfile.ZipFile(export_file_path, "r") as zin,
            zipfile.ZipFile(
                tmp_zip_path, "w", compression=zipfile.ZIP_DEFLATED
            ) as zout,
        ):
            for item in zin.infolist():
                if item.filename != "ro-crate-metadata.json":
                    zout.writestr(item, zin.read(item.filename))
            # Write modified metadata
            zout.writestr("ro-crate-metadata.json", json.dumps(metadata, indent=2))

        shutil.move(tmp_zip_path, export_file_path)

    # ============================================================================
    # EXPORT LOGIC
    # ============================================================================

    def export_rocrate(self):
        """Execute the RO-Crate export process"""
        metadata = self.get_export_metadata()
        try:
            # Validate required fields
            if not metadata["license"]:
                display_error_message(
                    self,
                    "License Required",
                    "Please select a license for your dataset.",
                )
                return

            # Validate ORCID format if provided
            if metadata["orcid"] and not self.validate_orcid(metadata["orcid"]):
                display_error_message(
                    self,
                    "Invalid ORCID",
                    "Please enter a valid ORCID in the format: 0000-0000-0000-0000",
                )
                return

            # Check if export directory exists
            if not os.path.exists(metadata["export_path"]):
                display_error_message(
                    self,
                    "Invalid Path",
                    "The selected export directory does not exist.",
                )
                return

            # Check if directory is writable
            if not os.access(metadata["export_path"], os.W_OK):
                display_error_message(
                    self,
                    "Permission Denied",
                    "Cannot write to the selected export directory.",
                )
                return

            # Disable export button during export
            self.export_PushButton.setEnabled(False)
            self.export_PushButton.setText("Exporting...")

            # Emit signal to start export process
            self.export_started.emit()

            export_file_path = os.path.join(
                metadata["export_path"],
                f"{re.sub(r'[^A-Za-z0-9]', '', metadata['title'])}.zip",
            )

            # Implement RO-Crate export logic
            start_time = time.perf_counter()
            crate = ROCrate()

            crate.root_dataset["name"] = str(metadata["title"])
            crate.root_dataset["description"] = str(metadata["description"])

            # Add license information
            license_url = self.get_license_url(metadata["license"])
            license_jsonld = {
                "@id": license_url if license_url else "#license",
                "@type": "CreativeWork",
                "name": str(metadata["license_name"]),
            }
            if license_url:
                license_jsonld["identifier"] = str(metadata["license"])
            crate.root_dataset["license"] = {"@id": license_jsonld["@id"]}
            self.logger.info(
                f"Adding license {license_jsonld['@id']} to crate."
            )
            crate.add_jsonld(license_jsonld)

            # Add author information
            author_jsonld = {
                "@id": (
                    f"https://orcid.org/{metadata['orcid']}"
                    if metadata["orcid"]
                    else "#author"
                ),
                "@type": "Person",
                "name": str(metadata["author"]),
            }
            if metadata["affiliation"]:
                author_jsonld["affiliation"] = str(metadata["affiliation"])
            crate.root_dataset["author"] = {"@id": author_jsonld["@id"]}
            self.logger.info(
                f"Adding author {author_jsonld['@id']} to crate."
            )
            crate.add_jsonld(author_jsonld)

            # Add QGIS software information
            crate.add_jsonld(
                {
                    "@id": "#qgis",
                    "@type": "SoftwareApplication",
                    "name": "QGIS",
                    "version": Qgis.QGIS_VERSION,
                }
            )
            self.logger.info("Added SoftwareApplication #qgis to crate.")

            # add documented layers
            for layer in self.parent.graph_tab.documented_layers.values():
                crate = layer.add_to_rocrate(crate)

            # add documented processes and their instruments
            instruments = {}
            for process in self.parent.graph_tab.documented_steps.values():
                instruments[process.instrument.id] = process.instrument
                crate = process.add_to_rocrate(crate)
            for instrument in instruments.values():
                crate = instrument.add_to_rocrate(crate)

            # Write RO-Crate to zip file and fix issues
            crate.write_zip(export_file_path)
            self._fix_rocrate_context(export_file_path)

            end_time = time.perf_counter()
            self.logger.info(
                f"Export completed in {end_time - start_time:.4f} seconds."
            )
            self.logger.info(f"Exported crate to {export_file_path}.")

            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"RO-Crate has been exported successfully to:\n{export_file_path}",
            )

            # Emit completion signal
            self.export_completed.emit(export_file_path)

        except Exception as e:
            # Handle any errors during export
            error_message = f"Export failed: {str(e)}"
            self.logger.error(e)
            display_error_message(self, "Export Error", error_message)
            self.export_failed.emit(error_message)

        finally:
            Logger().write_logs_to_file(metadata["export_path"], metadata["title"])
            # Re-enable export button and reset text
            self.validate_form()  # This will properly set the enabled state
            self.export_PushButton.setText("Export RO-Crate")
