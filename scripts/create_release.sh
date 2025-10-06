#!/bin/bash
set -e

VERSION=$1

# Function to sync tags with remote
sync_tags() {
    echo "Syncing tags with remote..."
    
    # Delete all local tags
    git tag -l | xargs -r git tag -d
    
    # Fetch tags from remote with prune
    git fetch --tags --prune
    
    echo "Local tags synced."
}

# Show help if no version provided
if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/create_release.sh v1.0.0"
    echo ""
    echo "Options:"
    echo "  --sync-tags    Sync local tags with remote before release"
    exit 1
fi

# Check for --sync-tags option
if [ "$VERSION" == "--sync-tags" ]; then
    sync_tags
    exit 0
fi

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

# Create and push tag
git tag -a "$VERSION" -m "Release $VERSION"
git push origin --tags

echo ""
echo "✅ Tag $VERSION created and pushed!"
echo "🚀 GitHub Actions is now building the release..."
echo "📊 Progress: https://github.com/nicevibesplus/qgis-workflow-documentation/actions"