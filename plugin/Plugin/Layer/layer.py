import re
import tempfile
from datetime import datetime
from os.path import getmtime, getsize, isfile
from pathlib import Path

from qgis.core import QgsMapLayer, QgsMapLayerType, QgsProject, QgsWkbTypes

from ..utility import get_logger, get_mimetype


class Layer:
    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, layer):
        """Initialize a Layer object from a QGIS layer.

        :param layer: The QGIS layer object to wrap
        :type layer: QgsMapLayer
        """
        self.logger = get_logger("Layer")
        self.external = False
        self.visible = bool(
            QgsProject.instance().layerTreeRoot().findLayer(layer.id()).isVisible()
        )
        self.layer = layer
        self.clean_name = re.sub(r"[^A-Za-z0-9]", "", layer.name())
        self.name = layer.name()
        self.description = ""
        self.type = (
            "Raster"
            if layer.type() == QgsMapLayer.RasterLayer
            else "Vector" if layer.type() == QgsMapLayer.VectorLayer else "Unknown"
        )
        self.provider = layer.dataProvider().name().lower()
        self.source = self.layer.source()
        self.sourceProperty = {}
        self.id = f"./{self.clean_name}"

    # ============================================================================
    # SETTERS / CONFIGURATION
    # ============================================================================

    def set_description(self, desc):
        """Set the description for this layer.

        :param desc: The description text for the layer
        :type desc: str
        """
        self.description = desc

    def set_external(self, ext):
        """Set whether this layer is from an external source.

        :param ext: True if the layer is external, False otherwise
        :type ext: bool
        """
        self.external = ext

    def set_external_source_properties(self, title, url, date, comment):
        """Set properties for external data sources.

        :param title: Title of the external data source
        :type title: str or None
        :param url: URL of the external data source
        :type url: str or None
        :param date: Date of the external data source
        :type date: str or None
        :param comment: Comment about the external data source
        :type comment: str or None
        """
        if title:
            self.sourceProperty["sourceTitle"] = str(title)
        if url:
            self.sourceProperty["sourceURL"] = str(url)
        if date:
            self.sourceProperty["sourceDate"] = str(date)
        if comment:
            self.sourceProperty["sourceComment"] = str(comment)

    # ============================================================================
    # UTILITY / HELPER METHODS
    # ============================================================================

    def _get_content_size(self, path):
        """Get the file size of a given path.

        :param path: File path to check
        :type path: str
        :return: File size as string with 'B' suffix, or 'Unknown' if file doesn't exist
        :rtype: str
        """
        if isfile(path):
            return f"{getsize(path) / 1024}"
        else:
            return "Unknown"

    def _get_last_modified(self, path):
        """Get the last modified timestamp of a file.

        :param path: File path to check
        :type path: str
        :return: Formatted timestamp string, or 'Unknown' if file doesn't exist
        :rtype: str
        """
        if isfile(path):
            # getting the last modified time using getmtime
            modified_time = getmtime(path)
            # formating the timestamp for readability
            formatted_time = datetime.fromtimestamp(modified_time).isoformat()
            return formatted_time
        else:
            return "Unknown"

    def _add_geometry_properties(self, props):
        if self.layer.crs():
            props["layerCrs"] = self.layer.crs().authid()
        if self.layer.type() is not None:
            props["layerType"] = QgsMapLayerType(self.layer.type()).name
        if self.layer.type() == QgsMapLayerType.VectorLayer:
            if self.layer.featureCount():
                props["layerFeatureCount"] = self.layer.featureCount()
            if self.layer.wkbType():
                props["layerGeometryType"] = QgsWkbTypes.displayString(
                    self.layer.wkbType()
                )
        return props

    def _add_source_properties(self, props):
        props.update(self.sourceProperty)
        return props

    def _add_encoding_property(self, props):
        # Determine proper MIME type based on file extension
        props["encodingFormat"] = get_mimetype(self.source)
        return props

    # ============================================================================
    # ROCRATE COMPONENT METHODS
    # ============================================================================

    def _add_dataset_to_rocrate(self, crate):
        """Add the layer dataset to the ROCrate.

        Creates a dataset entity in the ROCrate with the layer's name, description,
        and visibility properties.

        :param crate: The ROCrate object to add the dataset to
        :type crate: ROCrate
        :return: Tuple of the updated crate and the created dataset
        :rtype: tuple
        """
        # add dataset for map layer
        dataset = crate.add_dataset(
            dest_path=self.id,
            properties={
                "name": str(self.name),
                "description": str(self.description),
                "layerVisible": self.visible,
            },
        )
        self.logger.info(f"Added dataset {self.id} to crate.")

        return crate, dataset

    def _add_symbology_to_rocrate(self, crate):
        """Add the layer symbology file to the ROCrate.

        Exports the layer's style to a temporary QML file and adds it to the ROCrate
        with appropriate metadata including file size and modification date.

        :param crate: The ROCrate object to add the symbology to
        :type crate: ROCrate
        :return: Tuple of the updated crate and the created symbology file
        :rtype: tuple
        """
        # add symbology of map layer
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".qml", delete=False
        ) as temp_qml:
            temp_qml_path = temp_qml.name
            self.layer.saveNamedStyle(temp_qml_path)
            symbology = crate.add_file(
                temp_qml_path,
                f"{self.id}/symbology.qml",
                properties={
                    "name": f"{self.name} Symbology",
                    "encodingFormat": get_mimetype(temp_qml_path),
                    "contentSize": self._get_content_size(temp_qml_path),
                    "dateModified": self._get_last_modified(temp_qml_path),
                },
            )
            self.logger.info(
                f"Added file {temp_qml_path} -> "
                f"map/{self.clean_name}/symbology.qml to crate."
            )
            temp_qml.close()

        return crate, symbology

    def _add_geometry_to_rocrate(self, crate):
        """Add the layer geometry file to the ROCrate.

        Determines the appropriate MIME type based on file extension and adds
        the geometry file to the ROCrate with proper metadata properties including
        combined geometry and source properties.

        :param crate: The ROCrate object to add the geometry to
        :type crate: ROCrate
        :return: Tuple of the updated crate and the created geometry file
        :rtype: tuple
        """
        properties = {
            "name": f"{self.name} Geometry",
            "contentSize": self._get_content_size(self.source),
            "dateModified": self._get_last_modified(self.source),
        }
        properties = self._add_encoding_property(properties)
        properties = self._add_geometry_properties(properties)
        properties = self._add_source_properties(properties)
        geometry = crate.add_file(
            self.source,
            f"{self.id}/geometry{Path(self.source).suffix}",
            properties=properties,
        )
        self.logger.info(
            f"Added file {self.source} -> "
            f"map/{self.clean_name}/geometry{Path(self.source).suffix} to crate."
        )

        return crate, geometry

    # ============================================================================
    # PUBLIC INTERFACE
    # ============================================================================

    def add_to_rocrate(self, crate):
        """Add this layer and all its components to a ROCrate.

        This method orchestrates the addition of the layer dataset, symbology
        (if visible), and geometry files to the ROCrate. It also manages the
        hasPart relationships and removes individual components from the root
        dataset's hasPart to avoid duplication.

        :param crate: The ROCrate object to add this layer to
        :type crate: ROCrate
        :return: The updated ROCrate object
        :rtype: ROCrate
        """

        dataset = None
        crate, dataset = self._add_dataset_to_rocrate(crate)

        symbology = None
        if self.visible:
            crate, symbology = self._add_symbology_to_rocrate(crate)

        geometry = None
        crate, geometry = self._add_geometry_to_rocrate(crate)

        # Set hasPart relationship
        if self.visible and symbology:
            dataset["hasPart"] = [symbology, geometry]
        else:
            dataset["hasPart"] = [geometry]

        # IDs of parts you want to remove from root.hasPart
        ids_to_remove = [geometry["@id"]]
        if self.visible:
            ids_to_remove.append(symbology["@id"])

        # Replace with a filtered copy
        crate.root_dataset["hasPart"] = [
            part
            for part in crate.root_dataset.get("hasPart", [])
            if part["@id"] not in ids_to_remove
        ]

        return crate
