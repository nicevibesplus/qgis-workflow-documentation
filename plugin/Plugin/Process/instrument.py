# -*- coding: utf-8 -*-
"""
Instrument - Represents a QGIS processing algorithm as a software instrument
"""

from ..utility import get_logger


class Instrument:
    """Represents a QGIS processing algorithm as a software instrument"""

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, algorithm):
        """Initialize an Instrument from an algorithm ID.
        
        :param algorithm: QGIS algorithm identifier
        :type algorithm: str
        """
        self.logger = get_logger("Instrument")
        self.algorithm = algorithm
        self.id = f"#{algorithm}"
        self.type = "SoftwareApplication"
        self.name = f"QGIS: {algorithm}"

    # ============================================================================
    # ROCRATE EXPORT
    # ============================================================================

    def add_to_rocrate(self, crate):
        """Add this instrument to a ROCrate.
        
        :param crate: The ROCrate object to add this instrument to
        :type crate: ROCrate
        :return: The updated ROCrate object
        :rtype: ROCrate
        """
        crate.add_jsonld({"@id": self.id, "@type": self.type, "name": self.name})
        self.logger.info(f"Added instrument {self.id} to crate.")
        return crate