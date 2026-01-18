#!/bin/bash

# Zentel - Test Runner
# 린트 및 테스트를 실행합니다

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# 가상환경 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
else
    error "가상환경이 없습니다. 먼저 ./install.sh를 실행하세요."
    exit 1
fi

# .env 파일 로드
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 결과 저장
BACKEND_LINT="SKIP"
BACKEND_TEST="SKIP"
FRONTEND_LINT="SKIP"
FAILED=false

# 함수: 백엔드 린트
run_backend_lint() {
    info "Backend 린트 검사 중..."

    if [ -d "backend" ]; then
        cd backend
        if command -v ruff &> /dev/null; then
            if ruff check .; then
                BACKEND_LINT="PASS"
                success "Backend 린트 통과"
            else
                BACKEND_LINT="FAIL"
                error "Backend 린트 실패"
                FAILED=true
            fi
        else
            BACKEND_LINT="SKIP (ruff 없음)"
        fi
        cd ..
    fi
}

# 함수: 백엔드 테스트
run_backend_tests() {
    info "Backend 테스트 실행 중..."

    if [ -d "backend/tests" ]; then
        cd backend
        if pytest -v; then
            BACKEND_TEST="PASS"
            success "Backend 테스트 통과"
        else
            BACKEND_TEST="FAIL"
            error "Backend 테스트 실패"
            FAILED=true
        fi
        cd ..
    else
        BACKEND_TEST="SKIP (tests 폴더 없음)"
    fi
}

# 함수: 프론트엔드 린트
run_frontend_lint() {
    info "Frontend 린트 검사 중..."

    if [ -d "frontend" ]; then
        cd frontend
        if npm run lint; then
            FRONTEND_LINT="PASS"
            success "Frontend 린트 통과"
        else
            FRONTEND_LINT="FAIL"
            error "Frontend 린트 실패"
            FAILED=true
        fi
        cd ..
    fi
}

# 메인 로직
echo "=========================================="
echo "Zentel - Test Runner"
echo "=========================================="
echo ""

MODE=${1:-"all"}

case $MODE in
    "backend-lint")
        run_backend_lint
        ;;
    "backend-test")
        run_backend_tests
        ;;
    "frontend-lint")
        run_frontend_lint
        ;;
    "all"|*)
        run_backend_lint
        echo ""
        run_backend_tests
        echo ""
        run_frontend_lint
        ;;
esac

# 결과 테이블 출력
echo ""
echo "=========================================="
echo "테스트 결과"
echo "=========================================="
echo ""
echo "| 구분 | 결과 |"
echo "|------|------|"
echo "| Backend Lint | $BACKEND_LINT |"
echo "| Backend Test | $BACKEND_TEST |"
echo "| Frontend Lint | $FRONTEND_LINT |"
echo ""

if [ "$FAILED" = false ]; then
    echo -e "${GREEN}[최종 결과] PASS${NC}"
    exit 0
else
    echo -e "${RED}[최종 결과] FAIL${NC}"
    exit 1
fi
