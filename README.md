<img src="/images/icon.svg" align="right" width="100" />

# QFlowCrate
A QGIS plugin for semi-automatic documentation of geospatial workflows with standardized RO-Crate export to enhance reproducibility in map-based research.
<br clear="right"/>

## About This Project

This plugin was developed as part of a Bachelor's thesis in the Geoinformatics program at the University of Münster's Institute for Geoinformatics.

**Thesis Details:**
- **Title:** Enhancing Map Reproducibility: Developing a QGIS Plugin for Automated Documentation of Data Provenance and Workflow
- **Author:** Andreas Rademaker ([nicevibesplus](https://github.com/nicevibesplus))
- **Degree:** Bachelor of Science in Geoinformatics
- **Institution:** University of Münster, Institute for Geoinformatics
- **Supervisors:** Eftychia Koukouraki, Brian Ochieng Pondi
- **Date:** October 2025


## Installation
1. Download the latest plugin version from [Releases](https://github.com/nicevibesplus/qgis-workflow-documentation/releases)
2. Install in QGIS: Plugins -> Manage and Install Plugins -> Install from ZIP

## Development
### Prerequisites
* [QGIS](https://qgis.org/download/) (>=3.24)
* [uv](https://github.com/astral-sh/uv)
* git

### Setup Development Environment
1. Clone the Repository
First fork the repository to your GitHub account and then clone it locally:
```
git clone https://github.com/nicevibesplus/qgis-workflow-documentation.git  
cd qgis-workflow-documentation
```
2. Create Virtual Environment with uv
```
uv sync

# Linux/Mac/Git Bash
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### Release

```
# Linux/Git Bash
chmod +x scripts/create_release.sh
# Might need to commit changes to make it executable
scripts/create_release.sh v0.0.1

# Windows
scripts\create_release.sh v0.0.1
```
This packages only the prod necessary files and also the rocrate library dependencies to the ZIP.

## Troubleshooting

### ModuleNotFoundError: No module named 'rocrate'

**Issue:** When loading the plugin in QGIS, you encounter the following error:
```
ModuleNotFoundError: No module named 'rocrate'
Traceback (most recent call last):
  File "...", line 35, in classFactory
    from .automated_workflow_documentation import AutomatedWorkflowDocumentation
  ...
  File "...", line 32, in <module>
    from rocrate.rocrate import ROCrate
ModuleNotFoundError: No module named 'rocrate'
```

**Cause:** The `rocrate` package required by the plugin is not installed in QGIS's bundled Python environment. QGIS uses its own isolated Python interpreter, which is separate from your system Python.

**Solution:** Install the `rocrate` package to QGIS's Python site-packages directory. First, you need to identify which Python version is used by QGIS in your system. You can check this info at Help -> About in the top menu. For example, if the Python version pointed to by QGIS is 3.12.9, you should run the following command in your terminal:

1. **macOS/Linux:**
   ```bash
   python3 -m pip install --target ~/.local/lib/python3.12/site-packages rocrate
   ```

2. **Windows:**
   ```bash
   python -m pip install --target %APPDATA%\Python\Python312\site-packages rocrate
   ```

After installation, restart QGIS and the plugin should load without errors.
