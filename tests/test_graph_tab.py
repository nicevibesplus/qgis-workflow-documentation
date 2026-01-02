import re
from datetime import timedelta

import pytest
from qgis.testing import start_app
from qgis.PyQt.QtCore import QDateTime
from qgis.PyQt.QtWidgets import (
    QVBoxLayout
)

from plugin.Plugin.Graph.graph_tab import GraphTab

# ==========================================================================
# FIXTURES
# ==========================================================================

@pytest.fixture(scope="session")
def qgis_app():
    """Start QGIS application for tests."""
    yield start_app()


@pytest.fixture
def graph_tab(qgis_app):
    """Create a GraphTab"""
    graph_tab = GraphTab()
    yield graph_tab
    graph_tab.deleteLater()


# ==========================================================================
# FUNCTIONALITY TESTS
# ==========================================================================
def test_main_layout_exists(graph_tab):
    """Test that main layout is properly created"""
    layout = graph_tab.layout()
    assert layout is not None
    assert isinstance(layout, QVBoxLayout)

def test_main_layout_geometry(graph_tab):
    """Test that main layout has correct geometry"""
    layout = graph_tab.layout()
    assert layout.spacing() == 12

    margins = layout.contentsMargins()
    assert margins.left() == 10
    assert margins.top() == 10
    assert margins.right() == 10
    assert margins.bottom() == 10

def test_ui_components_exist(graph_tab):
    """UI components should exist with expected properties."""
    assert hasattr(graph_tab, "add_layer_btn")
    assert hasattr(graph_tab, "add_process_btn")
    assert hasattr(graph_tab, "connection_btn")
    assert hasattr(graph_tab, "clear_btn")
    assert hasattr(graph_tab, "graph_view")

def test_connection_button(graph_tab):
     # Check connection button is checkable
    assert graph_tab.connection_btn.isCheckable()

    # Toggle on
    graph_tab.toggle_connection_mode(True)
    assert graph_tab.graph_view.connection_mode is True

    # Toggle off
    graph_tab.toggle_connection_mode(False)
    assert graph_tab.graph_view.connection_mode is False

def test_graph_view_properties(graph_tab):
    """Test graph view is properly configured"""
    assert graph_tab.graph_view is not None
    assert graph_tab.graph_view.minimumHeight() == 400

    # Check tooltips exist
    assert graph_tab.add_layer_btn.toolTip() != ""
    assert graph_tab.add_process_btn.toolTip() != ""
    assert graph_tab.connection_btn.toolTip() != ""
    assert graph_tab.clear_btn.toolTip() != ""

def test_initialization(graph_tab):
    """Test that GraphTab initializes with empty state"""
    assert isinstance(graph_tab.documented_layers, dict)
    assert isinstance(graph_tab.documented_steps, dict)
    assert len(graph_tab.documented_layers) == 0
    assert len(graph_tab.documented_steps) == 0

def test_get_stats_empty(graph_tab):
    """Test stats for empty graph"""
    stats = graph_tab.get_stats()
    
    assert stats['layers'] == 0
    assert stats['processes'] == 0
    assert stats['total_nodes'] == 0


def test_get_stats_with_data(graph_tab):
    """Test stats with layers and processes"""
    class DummyLayer:
        def __init__(self, name):
            self.name = name

    class DummyProcess:
        def __init__(self, id_, name):
            self.id = id_
            self.name = name

    # Add layers and processes
    graph_tab.documented_layers["layer1"] = DummyLayer("layer1")
    graph_tab.documented_layers["layer2"] = DummyLayer("layer2")
    graph_tab.documented_steps["proc1"] = DummyProcess("proc1", "Process 1")

    stats = graph_tab.get_stats()
    
    assert stats['layers'] == 2
    assert stats['processes'] == 1
    assert stats['total_nodes'] == 3

def test_get_documented_steps(graph_tab):
    """Test get_documented_steps"""
    class DummyProcess:
        def __init__(self, id_, name):
            self.id = id_
            self.name = name

    # No steps initially
    steps = graph_tab.get_documented_steps()    
    assert isinstance(steps, dict)
    assert len(steps) == 0
    assert steps == {}
    
    # Add one step
    proc1 = DummyProcess("proc1", "Process 1")
    graph_tab.documented_steps["proc1"] = proc1

    steps = graph_tab.get_documented_steps()
    
    assert isinstance(steps, dict)
    assert len(steps) == 1
    assert "proc1" in steps
    assert steps["proc1"] == proc1

    # Add more steps
    proc2 = DummyProcess("proc2", "Process 2")
    proc3 = DummyProcess("proc3", "Process 3")
    
    graph_tab.documented_steps["proc2"] = proc2
    graph_tab.documented_steps["proc3"] = proc3
    
    steps = graph_tab.get_documented_steps()
    
    assert isinstance(steps, dict)
    assert len(steps) == 3
    assert "proc1" in steps
    assert "proc2" in steps
    assert "proc3" in steps
    assert steps["proc1"] == proc1
    assert steps["proc2"] == proc2
    assert steps["proc3"] == proc3

    # Remove one process
    graph_tab.on_process_removed(proc1)
    
    steps = graph_tab.get_documented_steps()
    
    assert len(steps) == 2
    assert "proc1" not in steps
    assert "proc2" in steps
    assert "proc3" in steps
    

def test_get_documented_layers(graph_tab):
    """Test get_documented_layers"""
    class DummyLayer:
        def __init__(self, name):
            self.name = name

    # No layers initially
    layers = graph_tab.get_documented_layers()
    
    assert isinstance(layers, dict)
    assert len(layers) == 0
    assert layers == {}
    
    # Add one layer
    layer1 = DummyLayer("Layer1")
    graph_tab.documented_layers["Layer1"] = layer1
    
    layers = graph_tab.get_documented_layers()
    
    assert isinstance(layers, dict)
    assert len(layers) == 1
    assert "Layer1" in layers
    assert layers["Layer1"] == layer1

    # Add more layers
    layer2 = DummyLayer("Layer2")
    layer3 = DummyLayer("Layer3")
    
    graph_tab.documented_layers["Layer2"] = layer2
    graph_tab.documented_layers["Layer3"] = layer3
    
    layers = graph_tab.get_documented_layers()
    
    assert isinstance(layers, dict)
    assert len(layers) == 3
    assert "Layer1" in layers
    assert "Layer2" in layers
    assert "Layer3" in layers
    assert layers["Layer1"] == layer1
    assert layers["Layer2"] == layer2
    assert layers["Layer3"] == layer3

    # Remove one layer
    graph_tab.on_layer_removed(layer1)
    
    layers = graph_tab.get_documented_layers()
    
    assert len(layers) == 2
    assert "Layer1" not in layers
    assert "Layer2" in layers
    assert "Layer3" in layers
