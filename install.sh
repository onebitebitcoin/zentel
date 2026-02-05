#!/bin/bash

# MyRottenApple - Installation Script
# 프로젝트 의존성을 설치하고 환경을 설정합니다

set -e  # 에러 발생 시 즉시 종료

echo "=========================================="
echo "MyRottenApple - Installation"
echo "=========================================="
echo ""

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 함수: 성공 메시지
success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# 함수: 경고 메시지
warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 함수: 에러 메시지
error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Node.js 확인
echo "1. Node.js 확인 중..."
if ! command -v node &> /dev/null; then
    error "Node.js가 설치되어 있지 않습니다."
    echo "   Node.js 18 이상을 설치해주세요: https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node -v)
success "Node.js $NODE_VERSION 발견"

# 2. Python 확인
echo ""
echo "2. Python 확인 중..."
if ! command -v python3 &> /dev/null; then
    error "Python3가 설치되어 있지 않습니다."
    echo "   Python 3.10 이상을 설치해주세요."
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
success "$PYTHON_VERSION 발견"

# 3. Python 가상환경 생성
echo ""
echo "3. Python 가상환경 생성 중..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "가상환경 생성 완료"
else
    warning "가상환경이 이미 존재합니다. 건너뜁니다."
fi

# 4. Python 가상환경 활성화
echo ""
echo "4. 가상환경 활성화 중..."
source venv/bin/activate
success "가상환경 활성화 완료"

# 5. Backend 의존성 설치
echo ""
echo "5. Backend 의존성 설치 중..."
if [ -f "backend/requirements.txt" ]; then
    cd backend
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
    success "Backend 패키지 설치 완료"
else
    warning "backend/requirements.txt가 없습니다. 백엔드 설치를 건너뜁니다."
fi

# 6. Frontend 의존성 설치
echo ""
echo "6. Frontend 의존성 설치 중..."
if [ -f "frontend/package.json" ]; then
    cd frontend
    npm install
    cd ..
    success "Frontend 패키지 설치 완료"
else
    warning "frontend/package.json이 없습니다. 프론트엔드 설치를 건너뜁니다."
fi

# 7. 환경 변수 파일 생성
echo ""
echo "7. 환경 변수 파일 확인 중..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        success ".env 파일 생성 완료"
    else
        warning ".env.example 파일이 없습니다."
        echo "   수동으로 .env 파일을 생성해주세요."
    fi
else
    success ".env 파일이 이미 존재합니다."
fi

# 완료
echo ""
echo "=========================================="
echo "설치가 완료되었습니다!"
echo "=========================================="
echo ""
echo "다음 명령으로 개발 서버를 시작할 수 있습니다:"
echo "  $ ./dev.sh"
echo ""
echo "테스트 실행:"
echo "  $ ./test.sh"
echo ""
echo "서버 주소:"
echo "  Frontend: http://localhost:6001"
echo "  Backend:  http://localhost:6000"
echo "  API Docs: http://localhost:6000/docs"
echo ""
