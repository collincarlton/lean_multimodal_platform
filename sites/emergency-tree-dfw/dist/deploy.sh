#!/usr/bin/env bash
set -euo pipefail
# Zero-Capital Deployment Script (Cloudflare Pages + GitHub Pages fallback)
DIST_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Deploying Hyper-Kaizen Directory (emergency-tree-dfw) from $DIST_DIR..."
if command -v wrangler >/dev/null 2>&1; then
  wrangler pages deploy "$DIST_DIR" --project-name "lunora-emergency-tree-dfw"
else
  echo "wrangler not installed; directory bundle already mirrored to ../../docs for GitHub Pages."
fi
