# -*- coding: utf-8 -*-
"""
Graph Tab Widget - Widget for creating layer relationship graphs
"""

import re

from qgis.core import QgsProject
from qgis.gui import QgsHistoryProviderRegistry
from qgis.PyQt.QtCore import QDateTime, Qt
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..Layer.layer_factory import LayerFactory
from ..Layer.layer_metadata_dialog import LayerMetadataDialog
from ..Process.process import Process
from ..Process.process_metadata_dialog import ProcessMetadataDialog
from ..utility import get_logger
from .graph_view import GraphView
from .layer_node import LayerNode
from .process_node import ProcessNode


class GraphTab(QWidget):
    """Widget for creating layer relationship graphs - can be added to tab widgets"""

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, parent=None):
        """Initialize the Graph tab widget.

        :param parent: Parent widget
        :type parent: QWidget
        """
        super().__init__(parent)
        self.logger = get_logger("LayerGraphWidget")

        # Track documented layers and processing steps
        self.documented_layers = {}  # layer_id: Layer object
        self.documented_steps = {}  # step_id: step object

        self.setup_ui()

    # ============================================================================
    # UI SETUP
    # ============================================================================

    def setup_ui(self):
        """Setup the UI without instructions"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        # Control buttons at the top
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.add_layer_btn = QPushButton("Add Layer")
        self.add_layer_btn.clicked.connect(self.open_add_layer_dialog)
        self.add_layer_btn.setToolTip(
            "Add layers from your QGIS project to document and visualize"
        )

        self.add_process_btn = QPushButton("Add Processing Step")
        self.add_process_btn.clicked.connect(self.open_add_process_dialog)
        self.add_process_btn.setToolTip(
            "Add processing steps from QGIS history to document your workflow"
        )

        self.connection_btn = QPushButton("Connection Mode")
        self.connection_btn.setCheckable(True)
        self.connection_btn.toggled.connect(self.toggle_connection_mode)
        self.connection_btn.setToolTip(
            "Enable to create connections between nodes by clicking them"
        )

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_graph)
        self.clear_btn.setToolTip("Remove all nodes and connections from the graph")

        button_layout.addWidget(self.add_layer_btn)
        button_layout.addWidget(self.add_process_btn)
        button_layout.addWidget(self.connection_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()  # Push buttons to the left

        main_layout.addLayout(button_layout)

        # Graph view (full width and height)
        self.graph_view = GraphView()
        self.graph_view.setMinimumHeight(400)  # Ensure adequate height
        main_layout.addWidget(self.graph_view)

        self.setLayout(main_layout)

    # ============================================================================
    # DIALOG METHODS
    # ============================================================================

    def open_add_layer_dialog(self):
        """Open dialog to select and add a layer to the graph"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Layer to Add")
        dialog.setMinimumSize(500, 350)

        layout = QVBoxLayout()

        # Create list widget with project layers
        layer_list = QListWidget()
        layer_list.setSelectionMode(QListWidget.MultiSelection)

        project = QgsProject.instance()
        available_layers = []

        for qgs_layer in project.mapLayers().values():
            if qgs_layer.name() not in self.documented_layers:
                available_layers.append(qgs_layer)

        if not available_layers:
            # No layers available
            no_layers_label = QLabel(
                "No undocumented layers found in the current QGIS project."
            )
            no_layers_label.setStyleSheet(
                "color: #6c757d; font-style: italic; padding: 20px;"
            )
            layout.addWidget(no_layers_label)
        else:
            # Add available layers to list
            for qgs_layer in available_layers:
                layer_type = (
                    qgs_layer.type().name
                    if hasattr(qgs_layer.type(), "name")
                    else str(qgs_layer.type())
                )
                item = QListWidgetItem(f"{qgs_layer.name()} ({layer_type})")
                item.setData(Qt.UserRole, qgs_layer)
                layer_list.addItem(item)

            layout.addWidget(layer_list)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if available_layers and dialog.exec_() == QDialog.Accepted:
            selected_items = layer_list.selectedItems()
            if selected_items:
                for item in selected_items:
                    qgs_layer = item.data(Qt.UserRole)

                    layer_obj = LayerFactory().create_layer(qgs_layer)

                    metadata_dialog = LayerMetadataDialog(parent=self, layer=layer_obj)

                    if metadata_dialog.exec_() == QDialog.Accepted:
                        # Layer has been documented, add to graph
                        node = LayerNode(layer_obj)
                        node.setPos(400, 300)  # Center position
                        self.graph_view.scene.addItem(node)

                        # Store in documented layers
                        self.documented_layers[layer_obj.name] = layer_obj

                        self.logger.info(f"Added layer to graph: {layer_obj.name}")

    def open_add_process_dialog(self):
        """Open dialog to select and add a processing step to the graph"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Processing Step")
        dialog.setMinimumSize(600, 450)

        layout = QVBoxLayout()

        # Create list widget with processing steps
        process_list = QListWidget()
        process_list.setSelectionMode(QListWidget.MultiSelection)

        # Add button to load older steps
        load_older_btn = QPushButton("Load Older Steps (>7 days)")
        load_older_btn.clicked.connect(
            lambda: self.populate_process_list(process_list, show_all=True)
        )
        load_older_btn.setStyleSheet(
            """
            QPushButton {
                padding: 6px 12px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )

        # Initially populate with recent steps only
        if not self.populate_process_list(process_list, show_all=False):
            # No recent steps found
            no_steps_label = QLabel(
                "No recent processing steps found. Click "
                "'Load Older Steps' to see older history, "
                "or run some processing tools in QGIS first."
            )
            no_steps_label.setStyleSheet(
                "color: #6c757d; font-style: italic; padding: 20px;"
            )
            no_steps_label.setWordWrap(True)
            layout.addWidget(no_steps_label)

        layout.addWidget(process_list)
        layout.addWidget(load_older_btn)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            selected_items = process_list.selectedItems()
            if selected_items:
                for item in selected_items:
                    step_data = item.data(Qt.UserRole)

                    process_obj = Process(step_data)

                    metadata_dialog = ProcessMetadataDialog(
                        parent=self, process=process_obj
                    )

                    if metadata_dialog.exec_() == QDialog.Accepted:
                        # Process has been documented, add to graph
                        node = ProcessNode(process_obj=process_obj)
                        node.setPos(400, 300)  # Center position
                        self.graph_view.scene.addItem(node)

                        # Store in documented steps
                        step_id = process_obj.id
                        self.documented_steps[step_id] = process_obj

                        self.logger.info(f"Added process to graph: {process_obj.name}")

    # ============================================================================
    # UTILITY / HELPER METHODS
    # ============================================================================

    def populate_process_list(self, process_list, show_all=False):
        """Populate the process list with steps, filtered by date if needed.

        :param process_list: List widget to populate
        :type process_list: QListWidget
        :param show_all: Whether to show all steps or only recent ones
        :type show_all: bool
        :return: True if steps were found, False otherwise
        :rtype: bool
        """
        process_list.clear()
        steps_found = False

        try:
            history_provider = QgsHistoryProviderRegistry()
            history_entries = history_provider.queryEntries()

            # Get current time and 7 days ago
            current_time = QDateTime.currentDateTime()
            seven_days_ago = current_time.addDays(-7)

            # Collect valid steps with their timestamps
            valid_steps = []

            for step in history_entries:
                entry = step.entry
                if entry:
                    algorithm = entry.get("algorithm_id", "Unknown")
                    timestamp = step.timestamp.toString("dd.MM.yyyy hh:mm:ss")
                    display_name = f"{timestamp} | {algorithm}"

                    # Skip if already documented
                    step_id = re.sub(r"[^A-Za-z0-9]", "", f"{algorithm}{timestamp}")
                    if step_id in self.documented_steps.keys():
                        continue

                    # Filter by date if not showing all
                    if not show_all and step.timestamp < seven_days_ago:
                        continue

                    valid_steps.append((step, display_name, entry))
                    steps_found = True

            # Sort by timestamp (newest first)
            valid_steps.sort(key=lambda x: x[0].timestamp, reverse=True)

            # Add sorted items to list
            for step, display_name, entry in valid_steps:
                item = QListWidgetItem(display_name)
                item.setData(Qt.UserRole, step)
                item.setToolTip(entry.get("log", "No additional information available"))
                process_list.addItem(item)

        except Exception as e:
            self.logger.error(f"Could not load processing history: {e}")

        return steps_found

    def toggle_connection_mode(self, enabled):
        """Toggle connection mode.

        :param enabled: Whether connection mode should be enabled
        :type enabled: bool
        """
        self.graph_view.toggle_connection_mode(enabled)
        if enabled:
            self.connection_btn.setText("Connection Mode (ON)")
            self.connection_btn.setToolTip(
                "Click two nodes to connect them. Click again to disable."
            )
        else:
            self.connection_btn.setText("Connection Mode")
            self.connection_btn.setToolTip(
                "Enable to create connections between nodes by clicking them"
            )

    def clear_graph(self):
        """Clear all items from graph"""
        if not self.documented_layers and not self.documented_steps:
            QMessageBox.information(
                self, "Nothing to Clear", "The graph is already empty."
            )
            return

        reply = QMessageBox.question(
            self,
            "Clear Graph",
            f"Are you sure you want to clear the entire graph?\n\n"
            f"This will remove:\n"
            f"• {len(self.documented_layers)} documented layers\n"
            f"• {len(self.documented_steps)} documented processing steps\n"
            f"• All connections between nodes",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.graph_view.scene.clear()
            self.documented_layers.clear()
            self.documented_steps.clear()

            # Reset connection mode
            self.connection_btn.setChecked(False)
            self.toggle_connection_mode(False)

            self.logger.info("Graph cleared.")

    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================

    def on_layer_removed(self, layer_obj):
        """Handle layer removal from the graph.

        :param layer_obj: Layer object that was removed
        :type layer_obj: Layer
        """
        # Find and remove the layer from stored layers
        for name, _ in list(self.documented_layers.items()):
            # Check if this is the same layer object
            if name == layer_obj.name:
                del self.documented_layers[name]
                self.logger.info(f"Removed layer from documentation: {name}")
                break

    def on_process_removed(self, process_obj):
        """Handle process removal from the graph.

        :param process_obj: Process object that was removed
        :type process_obj: Process
        """
        # Find and remove the process from stored steps
        for step_id, _ in list(self.documented_steps.items()):
            # Check if this is the same process object
            if step_id == process_obj.id:
                del self.documented_steps[step_id]
                self.logger.info(f"Removed process from documentation: {step_id}")
                break

    # ============================================================================
    # PUBLIC INTERFACE
    # ============================================================================

    def get_documented_layers(self):
        """Get all documented layers.

        :return: Dictionary of documented layers
        :rtype: dict
        """
        return self.documented_layers

    def get_documented_steps(self):
        """Get all documented processing steps.

        :return: Dictionary of documented processing steps
        :rtype: dict
        """
        return self.documented_steps

    def get_stats(self):
        """Get statistics about the current graph.

        :return: Dictionary containing graph statistics
        :rtype: dict
        """
        return {
            "layers": len(self.documented_layers),
            "processes": len(self.documented_steps),
            "total_nodes": len(self.documented_layers) + len(self.documented_steps),
        }
