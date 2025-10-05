#!/bin/bash
set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/prepare_release.sh v1.0.0"
    exit 1
fi

echo "=== Preparing release $VERSION ==="

# 1. Stelle sicher, dass wir auf dev sind
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "dev" ]; then
    echo "Error: Must be on dev branch"
    exit 1
fi

# 2. Stelle sicher, dass alles committed ist
if ! git diff-index --quiet HEAD --; then
    echo "Error: Uncommitted changes detected"
    exit 1
fi

# 3. Switch zu main und merge
echo "Switching to main..."
git checkout main
git merge dev --no-edit

# 4. Install production libs
echo "Installing production dependencies to libs/..."
rm -rf libs/
mkdir -p libs/
uv pip install --python-version 3.9 --target libs/ rocrate

# 5. Cleanup libs
echo "Cleaning up libs/..."
find libs/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find libs/ -type f -name "*.pyc" -delete
find libs/ -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find libs/ -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find libs/ -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

# 6. Commit libs
git add libs/
git add .gitignore
git commit -m "Release $VERSION: Update production dependencies" || true

# 7. Create tag
echo "Creating tag $VERSION..."
git tag -a $VERSION -m "Release $VERSION"

echo ""
echo "=== Release $VERSION prepared! ==="
echo ""
echo "Next steps:"
echo "  1. Review changes: git log -1"
echo "  2. Push: git push origin main --tags"
echo "  3. GitHub will automatically create the release"
echo ""
echo "To abort:"
echo "  git tag -d $VERSION"
echo "  git reset --hard HEAD~1"