#!/bin/zsh
set -euo pipefail

cd /Users/wmix/wmixclaude

echo "Regenerating index.html..."
python3 /Users/wmix/wmixclaude/build_v2.py

echo
read "GITHUB_USER?GitHub username:uguangxinlan-lgtm "
read -s "GITHUB_TOKEN?GitHub token: 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"
echo

git add .

if git diff --cached --quiet; then
  echo "No changes to commit."
else
  read "COMMIT_MSG?Commit message [update dashboard]: "
  COMMIT_MSG=${COMMIT_MSG:-update dashboard}
  git commit -m "$COMMIT_MSG"
fi

ORIGIN_URL="https://github.com/muguangxinlan-lgtm/wmix.git"
AUTH_URL="https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/muguangxinlan-lgtm/wmix.git"

git remote set-url origin "$ORIGIN_URL"
git push -u "$AUTH_URL" main
git remote set-url origin "$ORIGIN_URL"

echo
echo "Push finished."
echo "Then enable GitHub Pages in:"
echo "https://github.com/muguangxinlan-lgtm/wmix/settings/pages"
