#!/bin/zsh
set -euo pipefail

cd /Users/wmix/wmixclaude
exec /usr/bin/python3 /Users/wmix/wmixclaude/serve_dashboard.py --host 0.0.0.0 --port 8000
