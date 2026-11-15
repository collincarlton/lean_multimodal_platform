#!/usr/bin/env bash
# ==============================================================================
# deploy_gh_pages.sh — 1-Click Zero-Capital Deployment for Engine-1 Directory
# Target: GitHub Pages (via /docs folder on main) & Cloudflare Pages Fallback
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_DIR="$WORKSPACE_ROOT/docs"

echo "=== ENGINE-1 DIRECTORY DEPLOYMENT ==="
echo "Workspace: $WORKSPACE_ROOT"
echo "Docs Dir : $DOCS_DIR"

# 1. Pre-flight checks
if [ ! -d "$DOCS_DIR" ]; then
    echo "[-] Error: docs directory does not exist at $DOCS_DIR"
    exit 1
fi

if [ ! -f "$DOCS_DIR/index.html" ]; then
    echo "[-] Error: index.html not found in $DOCS_DIR"
    exit 1
fi

# Assert file size < 150 KB
INDEX_BYTES=$(wc -c < "$DOCS_DIR/index.html" | tr -d ' ')
if [ "$INDEX_BYTES" -gt 153600 ]; then
    echo "[-] Warning: index.html is $INDEX_BYTES bytes (> 150 KB limit)"
else
    echo "[✓] Verified index.html size: $INDEX_BYTES bytes (< 150 KB ceiling)"
fi

# Ensure .nojekyll exists
touch "$DOCS_DIR/.nojekyll"
echo "[✓] .nojekyll confirmed"

# 2. Check git status
cd "$WORKSPACE_ROOT"
if [ -d ".git" ]; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    echo "[✓] Git repo detected on branch '$CURRENT_BRANCH'"
    
    # Check if gh CLI is available
    if command -v gh &> /dev/null; then
        echo "[*] GitHub CLI (gh) detected. Verifying remote repository..."
        if git remote get-url origin &> /dev/null; then
            REPO_URL=$(git remote get-url origin)
            echo "[✓] Origin remote configured: $REPO_URL"
            echo "[*] Preparing commit of generated site..."
            git add docs/ sites/ engine1/ data/
            if git diff --staged --quiet; then
                echo "[✓] Working tree clean, nothing to commit."
            else
                git commit -m "feat(engine1): update pSEO static directory and modular pages [skip ci]"
                echo "[✓] Committed updated static directory assets."
            fi
            echo ""
            echo "To publish to GitHub Pages:"
            echo "  1. Ensure your repository settings under Settings > Pages are set to:"
            echo "     Source: Deploy from a branch"
            echo "     Branch: $CURRENT_BRANCH / /docs"
            echo "  2. Run: git push origin $CURRENT_BRANCH"
        else
            echo "[!] No origin remote configured. Local commit only."
        fi
    fi
fi

# 3. Cloudflare Pages Fallback
if command -v wrangler &> /dev/null; then
    echo ""
    echo "[*] Cloudflare Wrangler detected."
    echo "To deploy directly to Cloudflare Pages (Free Tier):"
    echo "  wrangler pages deploy docs --project-name=dfw-tree-service"
else
    echo "[i] Cloudflare Wrangler not installed. GitHub Pages /docs is primary."
fi

echo ""
echo "[✓] Engine-1 directory deployment bundle verified ready in $DOCS_DIR"
