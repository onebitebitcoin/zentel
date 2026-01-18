#!/bin/bash

# Zentel - Development Server
# 백엔드와 프론트엔드 개발 서버를 실행합니다

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# PID 파일 경로
BACKEND_PID_FILE=".backend.pid"
FRONTEND_PID_FILE=".frontend.pid"

# 함수: 메시지 출력
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 함수: 서버 종료
cleanup() {
    echo ""
    info "서버를 종료합니다..."

    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat $BACKEND_PID_FILE)
        kill $BACKEND_PID 2>/dev/null || true
        rm $BACKEND_PID_FILE
        success "백엔드 서버 종료"
    fi

    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat $FRONTEND_PID_FILE)
        kill $FRONTEND_PID 2>/dev/null || true
        rm $FRONTEND_PID_FILE
        success "프론트엔드 서버 종료"
    fi

    exit 0
}

# Ctrl+C 처리
trap cleanup INT TERM

# 로그 파일 초기화
info "로그 파일 초기화..."
rm -f backend/debug.log frontend/debug.log
success "로그 파일 초기화 완료"

# 함수: 백엔드 서버 시작
start_backend() {
    info "백엔드 서버 시작 중..."

    if [ ! -d "backend" ]; then
        error "backend/ 디렉토리가 없습니다."
        exit 1
    fi

    # 가상환경 활성화
    if [ ! -d "venv" ]; then
        error "가상환경이 없습니다. 먼저 ./install.sh를 실행하세요."
        exit 1
    fi

    source venv/bin/activate

    # .env 파일 로드
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi

    cd backend

    # Uvicorn으로 FastAPI 서버 시작
    uvicorn app.main:app --reload --host 0.0.0.0 --port 6000 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../$BACKEND_PID_FILE

    cd ..

    success "백엔드 서버 시작됨 (PID: $BACKEND_PID, Port: 6000)"
    echo "   API 문서: http://localhost:6000/docs"
}

# 함수: 프론트엔드 서버 시작
start_frontend() {
    info "프론트엔드 서버 시작 중..."

    if [ ! -d "frontend" ]; then
        error "frontend/ 디렉토리가 없습니다."
        exit 1
    fi

    cd frontend

    # Vite 개발 서버 시작
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../$FRONTEND_PID_FILE

    cd ..

    success "프론트엔드 서버 시작됨 (PID: $FRONTEND_PID, Port: 6001)"
    echo "   브라우저: http://localhost:6001"
}

# 메인 로직
echo "=========================================="
echo "Zentel - Development Server"
echo "=========================================="
echo ""

MODE=${1:-"all"}

case $MODE in
    "backend")
        start_backend
        ;;
    "frontend")
        start_frontend
        ;;
    "all"|*)
        start_backend
        echo ""
        sleep 2  # 백엔드 시작 대기
        start_frontend
        ;;
esac

echo ""
echo "=========================================="
echo "개발 서버가 실행 중입니다."
echo "종료하려면 Ctrl+C를 누르세요."
echo "=========================================="
echo ""

# 서버 로그 감시
wait
