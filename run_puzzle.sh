#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-4173}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[오류] python3가 필요합니다. 먼저 python3를 설치해 주세요." >&2
  exit 1
fi

echo "이미지 퍼즐 서버를 시작합니다..."
echo "경로: ${ROOT_DIR}"
echo "주소: http://localhost:${PORT}/index.html"
echo "중지하려면 Ctrl+C 를 누르세요."

cd "${ROOT_DIR}"
python3 -m http.server "${PORT}"
