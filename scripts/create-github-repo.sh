#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="${1:-repo-moi}"
OWNER="${2:-phanphan07111403-boop}"
VISIBILITY="${3:-public}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")/repo-moi"
TEMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Không tìm thấy thư mục dự án: $PROJECT_DIR"
  exit 1
fi

cp -a "$PROJECT_DIR/." "$TEMP_DIR/"
cd "$TEMP_DIR"

git init
git add .
git commit -m "Initial commit: khởi tạo ${REPO_NAME}"
git branch -M main

REMOTE_URL="https://github.com/${OWNER}/${REPO_NAME}.git"

echo "Đang tạo repository GitHub: ${OWNER}/${REPO_NAME} ..."

if gh repo create "${OWNER}/${REPO_NAME}" \
  --"${VISIBILITY}" \
  --description "Repository mới" \
  --source "$TEMP_DIR" \
  --remote origin \
  --push; then
  echo "Hoàn tất! Repository: https://github.com/${OWNER}/${REPO_NAME}"
else
  echo ""
  echo "Không thể tạo repo tự động. Tạo thủ công tại: https://github.com/new"
  echo "  Owner: ${OWNER}"
  echo "  Repository name: ${REPO_NAME}"
  echo ""
  echo "Sau khi tạo, chạy:"
  echo "  git remote add origin ${REMOTE_URL}"
  echo "  git push -u origin main"
fi
