import re
from urllib.parse import urlencode

from ..Layer.layer import Layer
from ..utility import get_logger, get_mimetype


class WFSLayer(Layer):
    """Specialized Layer subclass for handling QGIS WFS (Web Feature Service) layers.

    WFS layers are web-based vector data services that provide features over HTTP.
    This class handles parsing the WFS connection parameters from QGIS source strings
    and reconstructing proper WFS URLs for ROCrate storage.
    """

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, layer):
        """Initialize a WFSLayer from a QGIS WFS layer.

        Extracts and reconstructs the WFS service URL from the QGIS layer source
        to create a proper WFS GetFeature request URL.

        :param layer: The QGIS WFS layer object to wrap
        :type layer: QgsMapLayer
        """
        super().__init__(layer)
        self.logger = get_logger("WFSLayer")
        self.provider = "wfs"
        self.mimetype = None
        self.source = self._get_wfs_url()

    # ============================================================================
    # ROCRATE COMPONENT METHODS (OVERRIDES)
    # ============================================================================

    def _add_geometry_to_rocrate(self, crate):
        """Add the WFS layer reference to ROCrate.

        Since WFS layers are web services, this adds a reference to the service URL
        rather than downloading the actual data. The URL points to a GetFeature
        request that can be used to retrieve the layer data.

        :param crate: The ROCrate object to add the WFS reference to
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
        self.logger.info(f"Added WFS layer {self.source} to crate.")

        return crate, geometry

    # ============================================================================
    # UTILITY / HELPER METHODS
    # ============================================================================

    def _get_wfs_url(self):
        """Extract and reconstruct WFS URL from QGIS layer source string.

        Parses the QGIS source string to extract WFS service parameters and
        reconstructs a proper WFS GetFeature request URL with all necessary
        parameters like SERVICE, REQUEST, VERSION, TYPENAME, etc.

        :return: Complete WFS GetFeature URL or None if parsing fails
        :rtype: str or None
        """
        qgis_source_string = self.layer.source()
        request_type = "GetFeature"
        # Parameter aus der QGIS Source extrahieren
        params = {}

        # URL extrahieren
        url_match = re.search(r"url='([^']+)'", qgis_source_string)
        if not url_match:
            return None
        base_url = url_match.group(1)
        base_url = base_url.split("?")[0]

        # Standard WFS Parameter
        params["SERVICE"] = "WFS"
        params["REQUEST"] = request_type

        # Weitere Parameter aus Source extrahieren
        patterns = {
            "VERSION": r"VERSION=([^&\s']+)",
            "TYPENAME": r"TYPENAME=([^&\s']+)",
            "MAXFEATURES": r"MAXFEATURES=([^&\s']+)",
            "EXCEPTIONS": r"EXCEPTIONS=([^&\s']+)",
            "OUTPUTFORMAT": r"OUTPUTFORMAT=([^&\s']+)",
        }

        # Make parameter matching case-insensitive
        for key, pattern in patterns.items():
            match = re.search(pattern, qgis_source_string, re.IGNORECASE)
            if match:
                if key == "OUTPUTFORMAT":
                    self.mimetype = match.group(1).split("=")[1]
                params[key] = match.group(1)

        # URL zusammenbauen
        query_string = urlencode(params)
        return f"{base_url}?{query_string}"
