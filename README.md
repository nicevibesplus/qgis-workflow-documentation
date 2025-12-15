# QGIS Workflow Documentation Plugin

A QGIS plugin for semi-automatic documentation of geospatial workflows with standardized RO-Crate export to enhance reproducibility in map-based research.

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
git clone https://github.com/<your-username>/qgis-workflow-documentation.git 
cd qgis-workflow-documentation
```
2. Create Virtual Environment with uv
```
uv python install 3.12

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
