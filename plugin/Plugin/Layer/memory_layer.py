import tempfile

from qgis.core import QgsRasterFileWriter, QgsRasterPipe, QgsVectorFileWriter

from ..Layer.layer import Layer
from ..utility import get_logger, get_mimetype


class MemoryLayer(Layer):
    """Specialized Layer subclass for handling QGIS memory layers.

    Memory layers exist only in memory and don't have physical files on disk.
    This class handles exporting them to temporary files (TIFF for raster,
    GeoJSON for vector) before adding them to the ROCrate.
    """

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, layer):
        """Initialize a MemoryLayer from a QGIS memory layer.

        :param layer: The QGIS memory layer object to wrap
        :type layer: QgsMapLayer
        """
        super().__init__(layer)
        self.logger = get_logger("MemoryLayer")
        self.provider = "memory"
        self.source = "memory"

    # ============================================================================
    # ROCRATE COMPONENT METHODS (OVERRIDES)
    # ============================================================================

    def _add_geometry_to_rocrate(self, crate):
        """Add the memory layer geometry to ROCrate by exporting to temporary files.

        Since memory layers don't have physical files, this method exports them
        to temporary files first. Raster layers are exported as TIFF files,
        vector layers as GeoJSON files.

        :param crate: The ROCrate object to add the geometry to
        :type crate: ROCrate
        :return: Tuple of the updated crate and the created geometry file
        :rtype: tuple
        """
        geometry = None

        if self.type == "Raster":
            geometry = self._export_raster_to_rocrate(crate)
        elif self.type == "Vector":
            geometry = self._export_vector_to_rocrate(crate)

        return crate, geometry

    # ============================================================================
    # UTILITY / HELPER METHODS
    # ============================================================================

    def _export_raster_to_rocrate(self, crate):
        """Export memory raster layer to temporary TIFF file and add to ROCrate.

        :param crate: The ROCrate object to add the raster to
        :type crate: ROCrate
        :return: The created geometry file object
        :rtype: File
        """
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as temp_tif:
            temp_tif_path = temp_tif.name

        pipe = QgsRasterPipe()
        provider = self.layer.dataProvider()
        pipe.set(provider.clone())
        QgsRasterFileWriter(temp_tif_path).writeRaster(
            pipe,
            provider.xSize(),
            provider.ySize(),
            provider.extent(),
            provider.crs(),
        )

        properties = {
            "name": f"{self.name} Geometry",
            "encodingFormat": get_mimetype(temp_tif_path),
            "contentSize": self._get_content_size(temp_tif_path),
            "dateModified": self._get_last_modified(temp_tif_path),
        }
        properties = self._add_geometry_properties(properties)
        properties = self._add_source_properties(properties)

        geometry = crate.add_file(
            temp_tif_path,
            f"{self.id}/geometry.tif",
            properties=properties,
        )
        temp_tif.close()
        self.logger.info(
            f"Added memory file {temp_tif_path} -> {f'map/{self.clean_name}/geometry.tif'} to crate."
        )

        return geometry

    def _export_vector_to_rocrate(self, crate):
        """Export memory vector layer to temporary GeoJSON file and add to ROCrate.

        :param crate: The ROCrate object to add the vector to
        :type crate: ROCrate
        :return: The created geometry file object
        :rtype: File
        """
        with tempfile.NamedTemporaryFile(
            suffix=".geojson", delete=False
        ) as temp_geojson:
            temp_geojson_path = temp_geojson.name

        QgsVectorFileWriter.writeAsVectorFormat(
            self.layer,
            temp_geojson_path,
            "UTF-8",
            self.layer.crs(),
            "GeoJSON",
        )

        properties = {
            "name": f"{self.name} Geometry",
            "encodingFormat": get_mimetype(temp_geojson_path),
            "contentSize": self._get_content_size(temp_geojson_path),
            "dateModified": self._get_last_modified(temp_geojson_path),
        }
        properties = self._add_geometry_properties(properties)
        properties = self._add_source_properties(properties)

        geometry = crate.add_file(
            temp_geojson_path,
            f"{self.id}/geometry.geojson",
            properties=properties,
        )
        temp_geojson.close()
        self.logger.info(
            f"Added memory file {temp_geojson_path} -> {f'map/{self.clean_name}/geometry.geojson'} to crate."
        )

        return geometry
