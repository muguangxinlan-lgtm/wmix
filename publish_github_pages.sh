#!/bin/zsh
set -euo pipefail

cd /Users/wmix/wmixclaude

get_saved_credentials() {
  printf 'protocol=https\nhost=github.com\n\n' | git credential-osxkeychain get
}

save_credentials() {
  local user="$1"
  local token="$2"
  printf 'protocol=https\nhost=github.com\nusername=%s\npassword=%s\n\n' "$user" "$token" | git credential-osxkeychain store
}

echo "Regenerating index.html..."
python3 /Users/wmix/wmixclaude/build_v2.py

echo
CREDS="$(get_saved_credentials || true)"
GITHUB_USER="$(printf '%s\n' "$CREDS" | sed -n 's/^username=//p' | head -n 1)"
GITHUB_TOKEN="$(printf '%s\n' "$CREDS" | sed -n 's/^password=//p' | head -n 1)"

if [[ -z "${GITHUB_USER}" || -z "${GITHUB_TOKEN}" ]]; then
  read "GITHUB_USER?GitHub username: "
  read -s "GITHUB_TOKEN?GitHub token: "
  echo
  save_credentials "$GITHUB_USER" "$GITHUB_TOKEN"
  echo "Saved GitHub credentials to macOS Keychain."
else
  echo "Using GitHub credentials from macOS Keychain for ${GITHUB_USER}."
fi

git add .

if git diff --cached --quiet; then
  echo "No changes to commit."
else
  read "COMMIT_MSG?Commit message [update dashboard]: "
  COMMIT_MSG=${COMMIT_MSG:-update dashboard}
  git commit -m "$COMMIT_MSG"
fi

ORIGIN_URL="https://github.com/muguangxinlan-lgtm/wmix.git"

git remote set-url origin "$ORIGIN_URL"
git push -u origin main

echo
echo "Push finished."
echo "GitHub Pages settings:"
echo "https://github.com/muguangxinlan-lgtm/wmix/settings/pages"
