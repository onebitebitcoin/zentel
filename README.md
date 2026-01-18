# Bitcoin Cracker

> **웹 애플리케이션 개발을 위한 예시 샘플 프로젝트**

Bitcoin 블록체인 분석 및 주소 클러스터링 서비스의 풀스택 웹 애플리케이션 샘플입니다.

이 프로젝트는 React + FastAPI를 사용한 현대적인 웹 개발의 구조, 패턴, 베스트 프랙티스를 보여주는 **학습 및 참고용 자료**입니다.

## 목적

이 샘플 프로젝트는 다음을 보여줍니다:

- **풀스택 웹 개발 구조**: Frontend (React) + Backend (FastAPI) 분리
- **API 설계 패턴**: RESTful API 엔드포인트 구조
- **데이터베이스 설계**: PostgreSQL 스키마 및 관계 설계
- **개발 워크플로우**: 스크립트 기반 개발/테스트/배포 자동화
- **모던 UI/UX**: 디자인 시스템 및 컴포넌트 아키텍처

## 기술 스택

### Frontend
- React 18+ (Vite)
- Lucide React (아이콘)
- D3.js / vis.js (네트워크 그래프 시각화)
- TailwindCSS (스타일링)

### Backend
- Python 3.10+
- FastAPI (웹 프레임워크)
- SQLAlchemy (ORM)
- SQLite3 (데이터베이스)
- Bitcoin Core RPC (블록체인 데이터)

### DevOps
- Railway (배포)
- Docker (컨테이너화)
- Git (버전 관리)

## 프로젝트 구조

```
bitcoin-cracker/
├── frontend/           # React 프론트엔드
│   ├── src/
│   │   ├── components/ # UI 컴포넌트
│   │   ├── pages/      # 페이지
│   │   └── api/        # API 클라이언트
│   └── package.json
│
├── backend/            # FastAPI 백엔드
│   ├── app/
│   │   ├── api/        # API 라우터
│   │   ├── models/     # DB 모델
│   │   └── services/   # 비즈니스 로직
│   └── requirements.txt
│
├── .claude/            # Claude AI 설정
├── SPEC.md             # 상세 기술 문서
├── AGENTS.md           # 개발 가이드
├── install.sh          # 의존성 설치
├── dev.sh              # 개발 서버 실행
├── test.sh             # 테스트 실행
└── deploy.sh           # 배포 스크립트
```

## 빠른 시작

### 1. 의존성 설치

```bash
./install.sh
```

이 명령은 다음을 수행합니다:
- Python 가상환경 생성
- Backend pip 패키지 설치
- Frontend npm 패키지 설치
- 환경 변수 파일 생성

### 2. 개발 서버 실행

```bash
./dev.sh
```

다음 주소에서 접속:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API 문서: http://localhost:8000/docs

### 3. 테스트 실행

```bash
./test.sh              # 전체 테스트
./test.sh unit         # 유닛 테스트만
./test.sh --coverage   # 커버리지 포함
```

### 4. 배포

```bash
./deploy.sh            # Railway 배포
./deploy.sh --prod     # 프로덕션 배포
```

## 주요 기능

### 1. 주소 클러스터링
- Co-spending 휴리스틱을 사용한 주소 그룹핑
- Union-Find 알고리즘으로 효율적인 클러스터 관리

### 2. 트랜잭션 추적
- 입력/출력 추적
- 자금 흐름 시각화
- 시간별 트랜잭션 타임라인

### 3. 네트워크 시각화
- D3.js 기반 인터랙티브 그래프
- 주소 간 연결 관계 표시
- 클러스터별 색상 구분

### 4. 검색 및 필터링
- 주소/트랜잭션 ID 검색
- 기간별, 금액별 필터링
- 실시간 검색 결과

## 디자인 컨셉

이 프로젝트는 따뜻하고 친근한 디자인을 채택합니다:

- **색상**: 베이지, 크림, 오렌지, 골드 톤
- **테마**: 레트로/빈티지 베이킹 테마 (Toasty, Golden Trail 등)
- **레이아웃**: 카드 기반, 모바일 우선 반응형
- **인터랙션**: 부드러운 애니메이션 및 호버 효과

자세한 디자인 가이드는 [SPEC.md](./SPEC.md)의 "Design Reference" 섹션을 참고하세요.

## 개발 가이드

### 코딩 규칙
- [.claude/CLAUDE.md](./.claude/CLAUDE.md): 전반적인 프로젝트 규칙
- [AGENTS.md](./AGENTS.md): AI Agent 개발 규칙

### 주요 규칙
1. **이모지 금지**: 텍스트에서 이모지 사용하지 않음 (아이콘 컴포넌트 사용)
2. **중첩 카드 금지**: Card 내부에 Card를 중첩하지 않음
3. **모바일 우선**: Mobile-first 반응형 디자인
4. **한국 시간**: 모든 시간/날짜는 Asia/Seoul 기준
5. **명확한 에러**: fallback 더미 값 대신 명확한 에러 메시지

### API 문서
개발 서버 실행 후 http://localhost:8000/docs 에서 Swagger UI 문서를 확인할 수 있습니다.

## 환경 변수

`.env` 파일 예시:

```bash
# Backend
DATABASE_URL=sqlite:///./bitcoin_analysis.db
BITCOIN_RPC_HOST=localhost
BITCOIN_RPC_PORT=8332
BITCOIN_RPC_USER=bitcoinrpc
BITCOIN_RPC_PASSWORD=your_password
REDIS_URL=redis://localhost:6379

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Bitcoin Cracker
```

**데이터베이스**: SQLite3를 사용하여 별도 DB 서버 설치가 필요 없습니다.

## 배포

이 프로젝트는 Railway를 통해 배포하도록 설계되었습니다:

1. Railway CLI 설치: `npm install -g @railway/cli`
2. Railway 로그인: `railway login`
3. 배포: `./deploy.sh`

## 테스트

### Backend 테스트
```bash
cd backend
pytest tests/unit/           # 유닛 테스트
pytest tests/integration/    # 통합 테스트
pytest --cov=app             # 커버리지
```

### Frontend 테스트
```bash
cd frontend
npm run test                 # Jest/Vitest
npm run test:e2e            # Playwright E2E
```

## 기여

이 프로젝트는 학습 및 참고용 샘플입니다. 개선 사항이나 버그를 발견하면 Issue를 열거나 Pull Request를 보내주세요.

### 개발 워크플로우
1. 이슈 생성 또는 선택
2. 브랜치 생성: `git checkout -b feature/your-feature`
3. 코드 작성 및 테스트
4. 커밋: `git commit -m "feat: your feature"`
5. Push 및 PR 생성

## 라이선스

MIT License - 학습 및 참고 목적으로 자유롭게 사용하세요.

## 참고 자료

- [SPEC.md](./SPEC.md) - 상세 기술 명세서
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [React 문서](https://react.dev/)
- [Bitcoin Core RPC](https://developer.bitcoin.org/reference/rpc/)

## 연락처

질문이나 제안사항이 있으시면 Issue를 열어주세요.

---

**이 프로젝트는 웹 애플리케이션 개발의 예시 샘플입니다.**
실제 프로덕션 환경에 배포하기 전에 보안, 성능, 확장성을 추가로 고려해야 합니다.
