import glob
import os
import tempfile
import zipfile

from ..Layer.layer import Layer
from ..utility import get_logger


class SHPLayer(Layer):
    """Specialized Layer subclass for handling Shapefile layers."""

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, layer):
        """Initialize a SHPLayer from a QGIS layer.

        :param layer: The QGIS layer object to wrap
        :type layer: QgsMapLayer
        """
        super().__init__(layer)
        self.logger = get_logger("SHPLayer")
        self.mimetype = "application/zip"

    def _add_geometry_to_rocrate(self, crate):
        file_dir = os.path.dirname(self.source)
        file_basename = os.path.splitext(os.path.basename(self.source))[0]

        pattern = os.path.join(file_dir, f"{file_basename}.*")
        matching_files = glob.glob(pattern)

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            temp_zip_path = temp_zip.name

        with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in matching_files:
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname)

        properties = {
            "name": f"{self.name} Geometry",
            "encodingFormat": "application/zip",
            "contentSize": self._get_content_size(temp_zip_path),
            "dateModified": self._get_last_modified(temp_zip_path),
        }
        properties = self._add_geometry_properties(properties)
        properties = self._add_source_properties(properties)

        geometry = crate.add_file(
            temp_zip_path,
            f"{self.id}/geometry.zip",
            properties=properties,
        )
        temp_zip.close()
        self.logger.info(
            f"Added Shapefile archive {temp_zip_path} -> {f'map/{self.clean_name}/geometry.zip'} to crate."
        )

        return crate, geometry
