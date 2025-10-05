# -*- coding: utf-8 -*-
"""
Layer Node - Draggable layer node displayed as rectangle in graph view
"""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QBrush, QColor, QFont, QPen
from qgis.PyQt.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QMenu,
)

from ..Layer.layer_metadata_dialog import LayerMetadataDialog


class LayerNode(QGraphicsRectItem):
    """Draggable layer node - displayed as rectangle"""

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, layer_obj):
        """Initialize a LayerNode from a Layer object.

        :param layer_obj: Layer object to represent
        :type layer_obj: Layer
        """
        super().__init__(0, 0, 120, 60)
        self.layer_obj = layer_obj  # Reference to Layer object
        self.layer_name = getattr(layer_obj, "name", "Unnamed Layer")
        self.layer_type = getattr(layer_obj, "type", "Unknown")
        self.connections = []  # List of connected arrows
        self.input_arrows = []  # Arrows coming INTO this layer (only one allowed)

        # Set visual properties based on layer properties
        self.update_visual_style()

        # Make draggable and selectable
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        # Add text label with indicators
        self.text_item = QGraphicsTextItem("", self)
        self._setup_text_item()

    # ============================================================================
    # VISUAL STYLE
    # ============================================================================

    def update_visual_style(self):
        """Update visual style based on layer properties"""
        # Base color for layer type
        if self.layer_type == "Vector":
            base_color = QColor(100, 149, 237)
        else:
            base_color = QColor(255, 140, 0)

        # Modify styling for visibility
        visible = getattr(self.layer_obj, "visible", True)
        if not visible:
            # Make non-visible layers more muted
            base_color = base_color.darker(150)
            self.setPen(QPen(Qt.gray, 2, Qt.DashLine))  # Dashed border
        else:
            self.setPen(QPen(Qt.black, 2))  # Solid border

        # External layers get a different border style
        external = getattr(self.layer_obj, "external", False)
        if external:
            self.setPen(QPen(Qt.darkBlue, 3))  # Thicker blue border

        self.setBrush(QBrush(base_color))

    def _setup_text_item(self):
        """Setup text item to fit within the rectangle with visual indicators"""
        rect = self.rect()

        # Use layer.name if available, otherwise use layer_name
        display_name = getattr(self.layer_obj, "name", self.layer_name)

        # Create display text with indicators
        display_text = display_name

        # Add visual indicators
        indicators = []
        visible = getattr(self.layer_obj, "visible", True)
        external = getattr(self.layer_obj, "external", False)

        if visible:
            indicators.append("👁")  # Eye for visible layers
        if external:
            indicators.append("📖")  # Book for external layers

        if indicators:
            display_text = " ".join(indicators) + " " + display_text

        self.text_item.setPlainText(display_text)

        # Start with a reasonable font size
        font = QFont()
        font.setPointSize(10)
        self.text_item.setFont(font)

        # Calculate available space (with padding)
        available_width = rect.width() - 20
        available_height = rect.height() - 20

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

        # Create tooltip with full information
        layer_type_display = f"{self.layer_type} Layer"
        tooltip_parts = [f"{layer_type_display}: {display_name}"]

        if visible:
            tooltip_parts.append("Visible")
        else:
            tooltip_parts.append("Hidden")
        if external:
            tooltip_parts.append("External Source")

        self.setToolTip(" | ".join(tooltip_parts))

    def refresh_display(self):
        """Refresh the display after layer metadata changes"""
        self.layer_name = getattr(self.layer_obj, "name", "Unnamed Layer")
        self.layer_type = getattr(self.layer_obj, "type", "Unknown")
        self.update_visual_style()
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
            for arrow in self.connections + self.input_arrows:
                arrow.update_position()
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):  # noqa: N802
        """Right-click context menu.

        :param event: Context menu event
        :type event: QGraphicsSceneContextMenuEvent
        """
        menu = QMenu()
        inspect_action = menu.addAction("Inspect")
        delete_action = menu.addAction("Delete Layer")
        action = menu.exec_(event.screenPos())

        if action == inspect_action:
            self._inspect_layer()
        elif action == delete_action:
            self.delete_node()

    # ============================================================================
    # DIALOG METHODS
    # ============================================================================

    def _inspect_layer(self):
        """Open layer inspection dialog (read-only)"""
        dialog = LayerMetadataDialog(parent=None, layer=self.layer_obj)

        # Make dialog read-only
        self._make_dialog_readonly(dialog)

        # Change window title to indicate inspection mode
        layer_name = getattr(self.layer_obj, "name", "Unnamed Layer")
        dialog.setWindowTitle(f"Inspect Layer Metadata - {layer_name}")

        dialog.exec_()  # Show as modal dialog (no need to handle result)

    def _make_dialog_readonly(self, dialog):
        """Make all input fields in the dialog read-only.

        :param dialog: Dialog to make read-only
        :type dialog: LayerMetadataDialog
        """
        # Make text fields read-only
        if hasattr(dialog, "description_textedit"):
            dialog.description_textedit.setReadOnly(True)
        if hasattr(dialog, "source_title_lineedit"):
            dialog.source_title_lineedit.setReadOnly(True)
        if hasattr(dialog, "source_url_lineedit"):
            dialog.source_url_lineedit.setReadOnly(True)
        if hasattr(dialog, "source_date_dateedit"):
            dialog.source_date_dateedit.setReadOnly(True)
        if hasattr(dialog, "source_comment_textedit"):
            dialog.source_comment_textedit.setReadOnly(True)
        if hasattr(dialog, "external_checkbox"):
            dialog.external_checkbox.setEnabled(False)

        # Hide save button, only show cancel/close
        if hasattr(dialog, "save_button"):
            dialog.save_button.hide()
        if hasattr(dialog, "cancel_button"):
            dialog.cancel_button.setText("Close")

    # ============================================================================
    # CONNECTION MANAGEMENT
    # ============================================================================

    def can_accept_input_connection(self):
        """Check if this layer can accept another input connection.

        :return: True if layer can accept input, False otherwise
        :rtype: bool
        """
        return len(self.input_arrows) == 0  # Only allow one input connection

    def add_input_arrow(self, arrow):
        """Add an input arrow to this layer.

        :param arrow: Arrow to add
        :type arrow: ConnectionArrow
        :return: True if arrow was added, False otherwise
        :rtype: bool
        """
        if self.can_accept_input_connection():
            self.input_arrows.append(arrow)
            return True
        return False

    def remove_input_arrow(self, arrow):
        """Remove an input arrow from this layer.

        :param arrow: Arrow to remove
        :type arrow: ConnectionArrow
        """
        if arrow in self.input_arrows:
            self.input_arrows.remove(arrow)

    # ============================================================================
    # PUBLIC INTERFACE
    # ============================================================================

    def delete_node(self):
        """Remove node and all connections"""
        # Remove all connected arrows
        for arrow in self.connections[:]:
            arrow.remove_arrow()
        for arrow in self.input_arrows[:]:
            arrow.remove_arrow()

        # Notify parent widget about removal
        if hasattr(self.scene(), "views") and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view.parent(), "on_layer_removed"):
                view.parent().on_layer_removed(self.layer_obj)

        # Remove from scene
        self.scene().removeItem(self)
