# -*- coding: utf-8 -*-
"""
Process - Represents a QGIS processing step with metadata and RO-Crate export
"""

import re

from ..utility import get_logger
from .instrument import Instrument


class Process:
    """Represents a QGIS processing step"""

    # ============================================================================
    # INITIALIZATION
    # ============================================================================

    def __init__(self, source):
        """Initialize a Process from a QGIS history entry.

        :param source: QGIS history entry containing process information
        :type source: QgsHistoryEntry
        """
        self.logger = get_logger("Process")
        self.timestamp = source.timestamp.toString("dd.MM.yyyy hh:mm:ss")
        entry = source.entry
        self.algorithm_id = entry.get("algorithm_id")
        self.log = entry.get("log", "Unknown")
        self.process_command = entry.get("process_command", "Unknown")
        self.python_command = entry.get("python_command", "Unknown")
        self.parameters = entry.get("parameters", {})
        self.results = entry.get("results", {})
        self.id = re.sub(r"[^A-Za-z0-9]", "", f"{self.algorithm_id}{self.timestamp}")
        self.name = ""
        self.description = ""
        self.instrument = Instrument(self.algorithm_id)
        self.object = {}
        self.result = {}

    # ============================================================================
    # SETTERS / CONFIGURATION
    # ============================================================================

    def set_name_description(self, name, description):
        """Set the name and description for this process.

        :param name: Process name
        :type name: str
        :param description: Process description
        :type description: str
        """
        self.name = name
        self.description = description

    def set_input(self, inputs):
        """Set the input objects for this process.

        :param inputs: List of input layer IDs or single input layer ID
        :type inputs: list or str
        """
        if len(inputs) > 1:
            self.object = []
            for inp in inputs:
                self.object.append({"@id": inp})
        else:
            self.object = {"@id": inputs[0]}

    def set_result(self, result):
        """Set the result object for this process.

        :param result: Result layer ID
        :type result: str
        """
        self.result = {"@id": result}

    # ============================================================================
    # ROCRATE EXPORT
    # ============================================================================

    def add_to_rocrate(self, crate):
        """Add this process to a ROCrate.

        :param crate: The ROCrate object to add this process to
        :type crate: ROCrate
        :return: The updated ROCrate object
        :rtype: ROCrate
        """
        properties = {
            "name": str(self.name),
            "description": str(self.description),
            "qgisProcessCommand": str(self.process_command),
            "qgisPythonCommand": str(self.python_command),
            "qgisLog": str(self.log),
            "qgisParameters": str(self.parameters),
            "qgisResults": str(self.results),
        }

        crate.add_action(
            [{"@id": self.instrument.id}, {"@id": "#qgis"}],
            self.id,
            self.object,
            self.result,
            properties=properties,
        )

        self.logger.info(f"Added process {self.id} to crate.")
        return crate
