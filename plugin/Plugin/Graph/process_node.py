# -*- coding: utf-8 -*-
"""
Process Node - Draggable processing step node displayed as circle/oval in graph view
"""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QBrush, QColor, QFont, QPen
from qgis.PyQt.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsTextItem,
    QMenu,
)

from ..Process.process_metadata_dialog import ProcessMetadataDialog
from ..utility import get_logger


class ProcessNode(QGraphicsEllipseItem):
    """Draggable processing step node - displayed as circle/oval"""

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, process_obj):
        """Initialize a ProcessNode from a Process object.

        :param process_obj: Process object to represent
        :type process_obj: Process
        """
        super().__init__(0, 0, 120, 80)  # Slightly larger oval for processes
        self.logger = get_logger("ProcessNode")
        self.process_obj = process_obj  # Reference to Process object
        self.display_name = getattr(
            process_obj, "name", "Unnamed Process"
        )  # Fallback display name
        self.algorithm = getattr(
            process_obj, "algorithm_id", "Unknown"
        )  # Fallback algorithm
        self.input_arrows = []  # Arrows coming in
        self.output_arrows = []  # Arrows going out

        # Set visual properties
        self.setBrush(
            QBrush(QColor(144, 238, 144))
        )  # Light green for regular processes
        self.setPen(QPen(Qt.black, 2))

        # Make draggable and selectable
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        # Add text label
        self.text_item = QGraphicsTextItem("", self)
        self._setup_text_item()

    # ============================================================================
    # VISUAL STYLE
    # ============================================================================

    def _setup_text_item(self):
        """Setup text item to fit within the ellipse"""
        rect = self.rect()

        # Use process.name if available and not empty, otherwise use
        # display_name or algorithm
        if hasattr(self.process_obj, "name") and self.process_obj.name:
            process_name = self.process_obj.name
        elif self.display_name and self.display_name != "Unnamed Process":
            process_name = self.display_name
        else:
            process_name = self.algorithm

        self.text_item.setPlainText(process_name)

        # Start with a reasonable font size
        font = QFont()
        font.setPointSize(10)
        self.text_item.setFont(font)

        # Calculate available space (with padding) - ellipse is narrower than rectangle
        available_width = rect.width() - 30  # More padding for ellipse
        available_height = rect.height() - 30

        # Adjust font size to fit
        font_size = 10
        while font_size > 6:  # Minimum readable size
            font.setPointSize(font_size)
            self.text_item.setFont(font)

            # Set text width for word wrapping
            self.text_item.setTextWidth(available_width)

            # Check if it fits
            text_rect = self.text_item.boundingRect()
            if text_rect.height() <= available_height:
                break

            font_size -= 1

        # Center the text
        text_rect = self.text_item.boundingRect()
        x_offset = (rect.width() - text_rect.width()) / 2
        y_offset = (rect.height() - text_rect.height()) / 2
        self.text_item.setPos(x_offset, y_offset)

        # Create tooltip with process information
        algorithm_info = getattr(self.process_obj, "algorithm_id", self.algorithm)

        self.setToolTip(f"Process: {process_name} | Algorithm: {algorithm_info}")

    def refresh_display(self):
        """Refresh the display text after process metadata changes"""
        self._setup_text_item()

    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================

    def itemChange(self, change, value):  # noqa: N802
        """Update connected arrows when moved.

        :param change: Type of change
        :type change: QGraphicsItem.GraphicsItemChange
        :param value: New value
        :type value: QVariant
        :return: Result of parent itemChange
        :rtype: QVariant
        """
        if change == QGraphicsItem.ItemPositionChange:
            for arrow in self.input_arrows + self.output_arrows:
                arrow.update_position()
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):  # noqa: N802
        """Right-click context menu.

        :param event: Context menu event
        :type event: QGraphicsSceneContextMenuEvent
        """
        menu = QMenu()
        inspect_action = menu.addAction("Inspect")
        delete_action = menu.addAction("Delete Process")
        action = menu.exec_(event.screenPos())

        if action == inspect_action:
            self._inspect_process()
        elif action == delete_action:
            self.delete_node()

    # ============================================================================
    # DIALOG METHODS
    # ============================================================================

    def _inspect_process(self):
        """Open process inspection dialog (read-only)"""
        dialog = ProcessMetadataDialog(parent=None, process=self.process_obj)

        # Make dialog read-only
        self._make_dialog_readonly(dialog)

        # Change window title to indicate inspection mode
        process_name = getattr(self.process_obj, "name", "Unnamed Process")
        algorithm_id = getattr(self.process_obj, "algorithm_id", "Unknown")

        dialog.setWindowTitle(
            f"Inspect Process Metadata - "
            f"{process_name if process_name else algorithm_id}"
        )

        dialog.exec_()  # Show as modal dialog (no need to handle result)

    def _make_dialog_readonly(self, dialog):
        """Make all input fields in the dialog read-only.

        :param dialog: Dialog to make read-only
        :type dialog: ProcessMetadataDialog
        """
        # Make editable fields read-only
        if hasattr(dialog, "name_lineedit"):
            dialog.name_lineedit.setReadOnly(True)
        if hasattr(dialog, "description_textedit"):
            dialog.description_textedit.setReadOnly(True)

        # Hide save button, only show cancel/close
        if hasattr(dialog, "save_button"):
            dialog.save_button.hide()
        if hasattr(dialog, "cancel_button"):
            dialog.cancel_button.setText("Close")

    # ============================================================================
    # CONNECTION MANAGEMENT
    # ============================================================================

    def add_input_arrow(self, arrow):
        """Add an input arrow and update process object.

        :param arrow: Arrow to add
        :type arrow: ConnectionArrow
        """
        self.input_arrows.append(arrow)
        self._update_process_connections()

    def remove_input_arrow(self, arrow):
        """Remove an input arrow and update process object.

        :param arrow: Arrow to remove
        :type arrow: ConnectionArrow
        """
        if arrow in self.input_arrows:
            self.input_arrows.remove(arrow)
        self._update_process_connections()

    def add_output_arrow(self, arrow):
        """Add an output arrow and update process object.

        :param arrow: Arrow to add
        :type arrow: ConnectionArrow
        """
        self.output_arrows.append(arrow)
        self._update_process_connections()

    def remove_output_arrow(self, arrow):
        """Remove an output arrow and update process object.

        :param arrow: Arrow to remove
        :type arrow: ConnectionArrow
        """
        if arrow in self.output_arrows:
            self.output_arrows.remove(arrow)
        self._update_process_connections()

    def _update_process_connections(self):
        """Update process object's input and result based on connection arrows"""
        # Update input objects from incoming arrows
        input_layer_ids = []
        for arrow in self.input_arrows:
            # Get the source node (should be a LayerNode)
            if hasattr(arrow, "start_node") and hasattr(arrow.start_node, "layer_obj"):
                layer_id = arrow.start_node.layer_obj.id
                input_layer_ids.append(layer_id)

        # Set process inputs
        if input_layer_ids:
            self.process_obj.set_input(input_layer_ids)

        # Update result from outgoing arrows (should be only one layer as destination)
        result_layer_id = None
        for arrow in self.output_arrows:
            # Get the destination node (should be a LayerNode)
            if hasattr(arrow, "end_node") and hasattr(arrow.end_node, "layer_obj"):
                result_layer_id = arrow.end_node.layer_obj.id
                break  # Only take the first one as result

        # Set process result
        if result_layer_id:
            self.process_obj.set_result(result_layer_id)

        process_name = getattr(self.process_obj, "name", "Unnamed Process")
        self.logger.info(
            f"Updated process {process_name} connections: "
            f"\nInputs: {input_layer_ids}\nResult: {result_layer_id}"
        )

    # ============================================================================
    # PUBLIC INTERFACE
    # ============================================================================

    def delete_node(self):
        """Remove node and all connections"""
        # Remove all connected arrows
        for arrow in self.input_arrows[:] + self.output_arrows[:]:
            arrow.remove_arrow()

        # Notify parent widget about removal
        if hasattr(self.scene(), "views") and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view.parent(), "on_process_removed"):
                view.parent().on_process_removed(self.process_obj)
        # Remove from scene
        self.scene().removeItem(self)
