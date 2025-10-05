from urllib.parse import unquote

from ..Layer.layer import Layer
from ..utility import get_logger, get_mimetype


class WMSLayer(Layer):
    """Specialized Layer subclass for handling QGIS WMS (Web Map Service) layers.

    WMS layers are web-based raster data services that provide map images over HTTP.
    This class handles parsing the WMS connection parameters from QGIS source strings
    and reconstructing proper WMS URLs for ROCrate storage.
    """

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, layer):
        """Initialize a WMSLayer from a QGIS WMS layer.

        Extracts and reconstructs the WMS service URL from the QGIS layer source
        to create a proper WMS GetMap request URL.

        :param layer: The QGIS WMS layer object to wrap
        :type layer: QgsMapLayer
        """
        super().__init__(layer)
        self.logger = get_logger("WMSLyer")
        self.provider = "wms"
        self.mimetype = None
        self.source = self._get_wms_url()

    # ============================================================================
    # ROCRATE COMPONENT METHODS (OVERRIDES)
    # ============================================================================

    def _add_geometry_to_rocrate(self, crate):
        """Add the WMS layer reference to ROCrate.

        Since WMS layers are web services, this adds a reference to the service URL
        rather than downloading the actual data. The URL points to a GetMap
        request that can be used to retrieve the layer image.

        :param crate: The ROCrate object to add the WMS reference to
        :type crate: ROCrate
        :return: Tuple of the updated crate and the created geometry reference
        :rtype: tuple
        """
        properties = {
            "encodingFormat": (
                self.mimetype if self.mimetype else get_mimetype(self.source)
            ),
            "name": f"{self.name} Geometry",
        }
        properties = self._add_geometry_properties(properties)
        properties = self._add_source_properties(properties)
        geometry = crate.add_file(
            self.source,
            properties=properties,
        )
        self.logger.info(f"Added WMS layer {self.source} to crate.")

        return crate, geometry

    # ============================================================================
    # UTILITY / HELPER METHODS
    # ============================================================================

    def _get_wms_url(self):
        """Extract and reconstruct WMS URL from QGIS layer source string.

        Parses the QGIS source string to extract WMS service parameters and
        reconstructs a proper WMS GetMap request URL. Handles URL decoding
        and ensures required WMS parameters (SERVICE=WMS, REQUEST=GetMap) are present.

        :return: Complete WMS GetMap URL or None if parsing fails
        :rtype: str or None
        """
        # Extract base URL
        base_url = None
        params = []
        qgis_source = unquote(self.layer.source())

        # Split by & and process each part
        parts = qgis_source.split("&")

        for part in parts:
            if "url=" in part:
                base_url = part.split("url=")[1].rstrip("?")
            else:
                if "format=" in part:
                    self.mimetype = part.split("=")[1]
                params.append(part)

        if not base_url:
            return None

        # Add missing WMS parameters at the beginning
        wms_params = ["SERVICE=WMS", "REQUEST=GetMap"]

        # Combine all parameters
        all_params = wms_params + params

        # Build final URL
        return f"{base_url}?{'&'.join(all_params)}"
