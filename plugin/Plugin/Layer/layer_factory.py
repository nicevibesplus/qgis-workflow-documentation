from .gpkg_layer import GPKGLayer
from .layer import Layer
from .memory_layer import MemoryLayer
from .shp_layer import SHPLayer
from .wfs_layer import WFSLayer
from .wms_layer import WMSLayer


class LayerFactory:
    """Factory class for creating appropriate Layer objects based on provider type.

    This factory creates specific layer subclasses based on the QGIS layer's
    provider type, allowing for specialized handling of different layer types
    while maintaining a uniform interface.
    """

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self):
        self._layer_types = {
            "gdal": Layer,
            "ogr": Layer,
            "memory": MemoryLayer,
            "wms": WMSLayer,
            "wfs": WFSLayer,
        }

    # ============================================================================
    # PUBLIC INTERFACE
    # ============================================================================

    def create_layer(self, layer):
        """Create an appropriate Layer object based on the provider type.

        Examines the QGIS layer's provider type and returns an instance of the
        corresponding Layer subclass. Falls back to the base Layer class for
        unsupported provider types.

        :param layer: The QGIS layer object to wrap
        :type layer: QgsMapLayer
        :return: An instance of the appropriate Layer subclass
        :rtype: Layer
        """
        layer_type = layer.providerType().lower()
        if ".gpkg|layername=" in layer.source():
            return GPKGLayer(layer)
        if ".shp" in layer.source():
            return SHPLayer(layer)
        if layer_type in self._layer_types:
            return self._layer_types[layer_type](layer)
        return Layer(layer)
