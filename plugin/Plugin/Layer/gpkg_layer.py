from ..Layer.layer import Layer
from ..utility import get_logger


class GPKGLayer(Layer):
    """Specialized Layer subclass for handling GeoPackage layers."""

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, layer):
        """Initialize a GPKGLayer from a QGIS layer.

        :param layer: The QGIS layer object to wrap
        :type layer: QgsMapLayer
        """
        super().__init__(layer)
        self.logger = get_logger("GPKGLayer")
        self.mimetype = "application/geopackage+sqlite3"
        splits = layer.source().split("|layername=")
        self.source = splits[0]
        self.gpkg_layer = splits[1]

    def set_description(self, desc):
        desc = f"[GeoPackage Layer: {self.gpkg_layer}] {desc}"
        return super().set_description(desc)
