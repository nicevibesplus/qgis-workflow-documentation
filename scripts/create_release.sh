#!/bin/bash
set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/create_release.sh v1.0.0"
    exit 1
fi

# Check uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Error: Uncommitted changes detected!"
    exit 1
fi

# Create and push tag
git tag -a "$VERSION" -m "Release $VERSION"
git push origin --tags

echo ""
echo "Tag $VERSION pushed!"
echo "GitHub Actions is now building the release..."
echo "Check: https://github.com/nicevibesplus/qgis-workflow-documentation/actions"