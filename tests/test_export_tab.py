import os
import tempfile

import pytest
from qgis.testing import start_app
from qgis.PyQt.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
)

from plugin.Plugin.Export.export_tab import ExportTab

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def qgis_app():
    """Start QGIS application for tests."""
    yield start_app()


@pytest.fixture
def export_tab(qgis_app):
    """
    Fixture that creates the ExportTab widget.
    """
    export_tab = ExportTab()
    yield export_tab
    export_tab.deleteLater()


# ============================================================================
# COMPONENT TESTS
# ============================================================================
def test_main_layout_exists(export_tab):
    """Test that main layout is properly created"""
    layout = export_tab.layout()
    assert layout is not None
    assert isinstance(layout, QVBoxLayout)

def test_main_layout_geometry(export_tab):
    """Test that main layout has correct geometry"""
    layout = export_tab.layout()
    assert layout.spacing() == 12

    margins = layout.contentsMargins()
    assert margins.left() == 10
    assert margins.top() == 10
    assert margins.right() == 10
    assert margins.bottom() == 10


def test_ui_components_exist(export_tab):
    """Main UI components are present and have expected defaults."""
    assert export_tab.export_PushButton is not None
    assert export_tab.browse_PushButton is not None
    assert export_tab.title_LineEdit.placeholderText() == "Enter project title"
    assert export_tab.export_PushButton.text() == "Export RO-Crate"
    # By default the export button should be disabled
    assert not export_tab.export_PushButton.isEnabled()


def test_validate_orcid(export_tab):
    """ORCID validation accepts correct format and rejects invalid ones."""
    assert export_tab.validate_orcid("") # ORCID is optional
    assert export_tab.validate_orcid("0000-0000-0000-0000")
    assert export_tab.validate_orcid("0000-0000-0000-000X")
    assert not export_tab.validate_orcid("invalid-orcid")
    assert not export_tab.validate_orcid("123")

def test_get_license_url(export_tab):
    assert export_tab.get_license_url("CC0-1.0") == "https://creativecommons.org/publicdomain/zero/1.0/"
    assert export_tab.get_license_url("NON-EXISTENT") is None


def test_set_get_metadata(export_tab):
    export_tab.set_default_values(title="My Project", description="Desc", license_id="MIT")
    metadata = export_tab.get_export_metadata()
    assert metadata["title"] == "My Project"
    assert metadata["description"] == "Desc"
    assert metadata["license"] == "MIT"


def test_export_button(export_tab):
    export_tab.author_LineEdit.setText("Author")
    export_tab.orcid_LineEdit.setText("0000-0000-0000-0000")
    export_tab.affiliation_LineEdit.setText("Affiliation")
    index = export_tab.license_ComboBox.findData("CC0-1.0")
    export_tab.license_ComboBox.setCurrentIndex(index)
    export_tab.title_LineEdit.setText("T")
    export_tab.description_TextEdit.setPlainText("D")

    tmpdir = tempfile.mkdtemp() # Make a temporary path available
    export_tab.export_path_LineEdit.setText(tmpdir)

    # export_tab.validate_form()
    assert export_tab.export_PushButton.isEnabled()

    export_tab.clear_form()
    assert not export_tab.export_PushButton.isEnabled()

    os.rmdir(tmpdir)