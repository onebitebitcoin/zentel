#!/bin/bash

# Playwright 웹 스크래핑 샘플 실행 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${GREEN}Playwright 웹 스크래핑 샘플${NC}"
echo "================================================"

# 가상환경 활성화 확인
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${RED}Error: 가상환경이 없습니다. install.sh를 먼저 실행하세요.${NC}"
    exit 1
fi

# 가상환경 활성화
source "$PROJECT_ROOT/venv/bin/activate"

# Playwright 설치 확인
if ! python -c "import playwright" 2>/dev/null; then
    echo -e "${YELLOW}Playwright가 설치되지 않았습니다. 설치 중...${NC}"
    pip install playwright
    playwright install chromium
fi

# Chromium 브라우저 설치 확인
if ! playwright show-trace --help >/dev/null 2>&1; then
    echo -e "${YELLOW}Chromium 브라우저를 설치 중...${NC}"
    playwright install chromium
fi

# URL 인자 확인 (기본값: example.com)
URL="${1:-https://example.com}"

echo -e "URL: ${GREEN}$URL${NC}"
echo "================================================"
echo ""

# 스크립트 실행
cd "$SCRIPT_DIR"
python playwright_scraper.py --url "$URL" --pretty

# Exit code 전달
exit $?
