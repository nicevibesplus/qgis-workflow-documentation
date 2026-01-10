# Plugin Functionality Tests 

This directory contains the pytest-based unit and component tests for the plugin.

## Prerequisites

QGIS must be installed in your computer. To ensure compatibility with your QGIS installation behavior, you should run the tests from a Python environment that can access the QGIS installation (usually this is your system Python). Pytest should also be installed.


## Running the tests

Navigate to the root directory of the github repository, then run the following command: 

```bash
python3 -m pytest ./tests/ 
```

Run a single test file:

```bash
python3 -m pytest ./tests/test_graph_tab.py
```

Helpful flags:
- `-v` — verbose output


## Fixture notes

- `qgis_app` fixture (defined in the tests) calls `qgis.testing.start_app()` and ensures a QGIS/Qt application is running for GUI functionality tests.
- GUI widgets created in tests are typically cleaned up with `.deleteLater()` in teardown to avoid memory leaks.