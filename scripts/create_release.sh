#!/bin/bash
set -e

VERSION=$1
METADATA_FILE="metadata.txt"

# Show help if no version provided
if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/create_release.sh v1.0.0"
    echo ""
    echo "Current version: $(grep '^version=' $METADATA_FILE 2>/dev/null | cut -d'=' -f2 || echo 'not set')"
    echo ""
    echo "Options:"
    echo "  --sync-tags    Sync local tags with remote before release"
    exit 1
fi

# Function to sync tags with remote
sync_tags() {
    echo "Syncing tags with remote..."
    git tag -l | xargs -r git tag -d
    git fetch --tags --prune
    echo "Local tags synced."
}

# Check for --sync-tags option
if [ "$VERSION" == "--sync-tags" ]; then
    sync_tags
    exit 0
fi

# Validate version format (semantic versioning)
if ! [[ $VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must follow semantic versioning format: v1.0.0"
    exit 1
fi

# Extract version without 'v' prefix for metadata.txt
VERSION_NUMBER="${VERSION#v}"

# Check uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Error: Uncommitted changes detected!"
    exit 1
fi

# Optional: Sync tags before release
read -p "Do you want to sync tags first? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sync_tags
fi

# Check if tag already exists
if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "Error: Tag $VERSION already exists!"
    echo "Existing tags:"
    git tag -l
    exit 1
fi

# Update metadata.txt
echo "Updating $METADATA_FILE to version $VERSION_NUMBER..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^version=.*/version=$VERSION_NUMBER/" "$METADATA_FILE"
else
    # Linux
    sed -i "s/^version=.*/version=$VERSION_NUMBER/" "$METADATA_FILE"
fi

# Show changes
echo ""
echo "Changes to be committed:"
git diff "$METADATA_FILE"

# Confirm changes
read -p "Proceed with commit and release? (y/N) " -n 1 -r
echo
if ! [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Release cancelled."
    git checkout "$METADATA_FILE"
    exit 0
fi

# Commit metadata file
git add "$METADATA_FILE"
git commit -m "Bump version to $VERSION"

# Create and push tag
git tag -a "$VERSION" -m "Release $VERSION"

# Push changes and tags
git push origin main
git push origin --tags

echo ""
echo "Version updated in $METADATA_FILE: $VERSION_NUMBER"
echo "Tag $VERSION created and pushed!"
echo "GitHub Actions is now building the release..."
echo "Progress: https://github.com/nicevibesplus/qgis-workflow-documentation/actions"