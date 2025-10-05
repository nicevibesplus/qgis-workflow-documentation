# QGIS Workflow Documentation

A QGIS plugin for documenting geospatial workflows and exporting them as RO-Crate packages to enhance reproducibility in GIS projects. This plugin is the result of a Bachelor's Thesis by @nicevibesplus. 

## Installation
1. Download the latest plugin version from [Releases](https://github.com/nicevibesplus/qgis-workflow-documentation/releases)
2. Install in QGIS: \
Plugins -> Manage and Install Plugins -> Install from ZIP

## Development
### Prerequisites
* [QGIS](https://qgis.org/download/) (>=3.24)
* [uv](https://github.com/astral-sh/uv)
* git

### Setup Development Environment
1. Clone the Repository
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