#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: ./scripts/push-to-github.sh <repository-url>"
  exit 1
fi

git init
git branch -M main
git add .
git commit -m "Initial Emerald leave system"
git remote add origin "$1"
git push -u origin main
