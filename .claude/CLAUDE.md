# Claude Project Rules

## Language
- 모든 답변은 한국어로 작성한다.
- 코드/로그/에러 메시지는 원문 유지, 설명은 한국어로 한다.

## Writing / UI Guidelines
1) 이모지를 사용하지 말고 아이콘을 사용할 것
   - 텍스트에서 이모지 금지
   - UI에서는 아이콘 컴포넌트(예: lucide-react) 사용

2) **중첩된 카드뷰는 사용하지 말 것 (CRITICAL)**
   - Card 내부에 Card 중첩 금지
   - 섹션 분리는 divider/heading/spacing/background로 처리
   - 레이아웃 깊이는 최대 2단계까지만 허용

3) **심플한 디자인 유지 (CRITICAL)**
   - 웹 UI에 너무 많은 텍스트 설명 표시 금지
   - 긴 설명문, 상세 가이드는 최소화
   - 필요한 정보만 간결하게 표시
   - 상세 정보는 툴팁/모달로 숨김 처리
   - "Less is more" 원칙

4) **모바일 친화적인 레이아웃으로 적용할 것 (CRITICAL)**
   - Mobile-first 레이아웃 원칙
   - 작은 화면 가독성/터치 타깃 최우선
   - **모바일 좌우 padding은 최소한으로 설정** (예: px-2 또는 px-4)
   - 항상 UI 업데이트 시 모바일에서 어떻게 보일지 고려

   **사용자 요청 확인 (CRITICAL)**:
   - 사용자의 UI 요청이 웹에만 한정되어 너무 디테일하면 반드시 되물을 것
   - 질문 예시: "이렇게 업데이트하면 모바일에서 레이아웃이 깨질 수 있는데 괜찮나요?"
   - 모바일 호환성을 사용자에게 확인받고 진행

5) 시간/날짜는 항상 한국 시간(Asia/Seoul)을 기준으로 판단한다.

6) fallback 더미 값 주입으로 흐름을 숨기지 말 것
   - 디버깅을 어렵게 하므로 기본/더미 값으로 덮어쓰지 않는다.
   - 문제가 발생하면 에러 메시지를 명확히 노출한다.

7) 사용자 작업에는 성공/실패 메시지를 항상 노출할 것
   - 저장/추가/삭제/새로고침 등 주요 액션의 결과를 명확히 표시한다.

8) **디자인 레퍼런스 확인 (CRITICAL)**
   - UI 작업 전 `design/reference/` 폴더에 레퍼런스 이미지가 있는지 확인
   - 이미지가 있으면 해당 스타일을 분석하여 적용
   - 이미지가 없으면 사용자에게 디자인 방향을 질문:
     ```
     "design/reference 폴더에 레퍼런스 이미지가 없습니다.
     어떤 스타일로 디자인할까요?
     1. 깔끔한 미니멀 스타일
     2. 금융 앱 스타일 (토스, 뱅크샐러드)
     3. 기본 TailwindCSS 스타일
     4. 직접 설명해주세요"
     ```
   - 레퍼런스 이미지 확인 후 UI 컴포넌트 개발 시작

## Workflow
- 코드 수정 후 항상:
  1) **Lint 체크 (테스트 전 필수)**
     - Frontend (React): `npm run lint` (ESLint)
     - Backend (FastAPI): `ruff check .` 또는 `flake8`
     - 에러가 있으면 수정 후 다시 체크
  2) 테스트 실행 → PASS/FAIL 확인
  3) **테스트 결과를 테이블 형태로 출력 (필수)**
  4) FAIL이면 수정 후 재테스트
  5) **PASS면 반드시 `git add` → `git commit` 수행 (절대 누락 금지)**
  6) `git push`는 사용자가 명시적으로 요청할 때만 수행

### 기능 추가 시 테스트 자동 작성 (CRITICAL)
**새로운 기능을 추가하면 반드시 해당 기능의 테스트 코드도 함께 작성해야 한다.**

1. **Backend 기능 추가 시**:
   - `backend/tests/` 폴더에 테스트 추가
   - 해당 API 엔드포인트의 성공/실패 케이스 테스트
   - 엣지 케이스 및 유효성 검증 테스트

2. **Frontend 기능 추가 시**:
   - `frontend/src/**/*.test.ts` 파일에 테스트 추가
   - 컴포넌트/훅/유틸리티 함수 테스트

3. **테스트 시나리오 예시**:
   - 정상 동작 케이스 (Happy Path)
   - 에러 케이스 (잘못된 입력, 권한 없음 등)
   - 엣지 케이스 (빈 값, 경계값 등)
   - 필터/검색 등 조합 케이스

### Commit 필수 (CRITICAL)
**테스트 통과 후 commit을 절대 잊지 말 것!**
- 작업 완료 + 테스트 PASS → 반드시 commit
- commit 없이 다음 작업으로 넘어가지 말 것
- 사용자가 commit 하지 말라고 명시적으로 요청한 경우에만 생략

### 테스트 결과 출력 형식 (필수)
테스트 수행 후 반드시 아래 형식으로 결과를 출력한다:

```
| 구분 | 결과 | 상세 |
|------|------|------|
| Frontend Lint | PASS/FAIL | 에러 수 또는 "OK" |
| Backend Lint | PASS/FAIL | 에러 수 또는 "OK" |
| Frontend Test | PASS/FAIL | 통과/전체 (예: 10/10) |
| Backend Test | PASS/FAIL | 통과/전체 (예: 15/15) |
| **최종 결과** | **PASS/FAIL** | - |
```

### Lint 설정

**Frontend (React) - ESLint**:
```bash
# 린트 체크
npm run lint

# 자동 수정
npm run lint -- --fix
```

**Backend (FastAPI) - Ruff**:
```bash
# 린트 체크
ruff check .

# 자동 수정
ruff check . --fix

# 포맷팅
ruff format .
```

### 테스트 실행 명령

사용자가 "테스트 실행해줘", "frontend 테스트", "backend 테스트" 등을 요청하면 아래 명령을 실행한다.

**Frontend 테스트**:
```bash
cd frontend && npm test
# 또는 vitest 사용 시
cd frontend && npm run test
```

**Backend 테스트**:
```bash
cd backend && python3 -m pytest tests/ -v --tb=short
```

**전체 테스트**:
```bash
# Frontend + Backend 모두 실행
cd frontend && npm run lint && npm test
cd backend && python3 -m pytest tests/ -v --tb=short
```

### 테스트 파일 위치

| 구분 | 위치 | 패턴 |
|------|------|------|
| Backend | `backend/tests/` | `test_*.py` |
| Frontend | `frontend/src/**/*.test.ts` | `*.test.ts`, `*.spec.ts` |
| Frontend | `frontend/src/**/*.test.tsx` | `*.test.tsx`, `*.spec.tsx` |

## Database & API Synchronization (CRITICAL)
**스키마와 API는 항상 함께 업데이트되어야 한다.**

- 데이터베이스 스키마가 변경되면 반드시 관련 API도 함께 업데이트해야 함
- CRUD 기능 개발/수정 시 스키마와 API를 항상 같이 취급할 것
- 스키마만 업데이트하고 API를 업데이트하지 않으면 불일치가 발생함

**예시**:
- 스키마에 새 필드 추가 → API response model에도 필드 추가
- 스키마에서 필드 제거 → API에서도 해당 필드 제거
- 스키마 필드 타입 변경 → API validation/serialization 로직도 변경

**체크리스트**:
1. 스키마 변경 시 영향받는 모든 API 엔드포인트 확인
2. Pydantic 모델 (request/response) 업데이트
3. API 문서 (Swagger) 자동 반영 확인
4. 테스트 코드 업데이트

## Backend Development - Unix Philosophy (CRITICAL)

**Backend 개발 시 반드시 Unix Philosophy를 따라야 한다.**

Unix Philosophy는 Ken Thompson이 시작하고 Eric Raymond가 정리한 소프트웨어 설계 원칙이다.
참고: https://en.wikipedia.org/wiki/Unix_philosophy

### 17가지 원칙

| # | 원칙 | 설명 | 적용 예시 |
|---|------|------|----------|
| 1 | **Modularity** | 단순한 부분들을 깔끔한 인터페이스로 연결 | 작은 함수/클래스, 명확한 책임 분리 |
| 2 | **Clarity** | 명확함이 영리함보다 낫다 | 트릭 코드 금지, 읽기 쉬운 코드 작성 |
| 3 | **Composition** | 프로그램들이 서로 연결되도록 설계 | 재사용 가능한 모듈, 표준 인터페이스 |
| 4 | **Separation** | 정책과 메커니즘 분리, 인터페이스와 엔진 분리 | 비즈니스 로직과 데이터 접근 분리 |
| 5 | **Simplicity** | 단순성을 위해 설계, 필요한 곳에만 복잡성 추가 | YAGNI 원칙, 과도한 추상화 금지 |
| 6 | **Parsimony** | 큰 프로그램은 필요가 명확히 입증될 때만 작성 | 작은 모듈 선호, 거대 클래스 금지 |
| 7 | **Transparency** | 검사와 디버깅을 용이하게 가시성 확보 | 명확한 로깅, 상태 추적 가능 |
| 8 | **Robustness** | 견고함은 투명성과 단순성의 산물 | 엣지 케이스 처리, 예외 처리 |
| 9 | **Representation** | 데이터에 지식을 담아 프로그램 로직을 단순하게 | 데이터 구조 활용, 하드코딩 금지 |
| 10 | **Least Surprise** | 가장 예상 가능한 동작 수행 | 일관된 API, 표준 컨벤션 준수 |
| 11 | **Silence** | 할 말이 없으면 침묵 | 불필요한 출력 금지, 필요한 정보만 |
| 12 | **Repair** | 실패할 때는 명확하고 빠르게 실패 | 빠른 실패, 명확한 에러 메시지 |
| 13 | **Economy** | 프로그래머 시간은 비싸다, 기계 시간보다 우선 | 가독성 우선, 조기 최적화 금지 |
| 14 | **Generation** | 손으로 작성하지 말고 프로그램이 코드 생성 | 코드 생성기, 메타프로그래밍 활용 |
| 15 | **Optimization** | 프로토타입 먼저, 작동 후 최적화 | 먼저 동작하게, 나중에 빠르게 |
| 16 | **Diversity** | "유일한 방법" 주장을 의심 | 다양한 접근법 허용, 독단 금지 |
| 17 | **Extensibility** | 미래를 위해 설계 | 확장 가능한 구조, 플러그인 지원 |

### 필수 체크리스트

```
[ ] 각 모듈/함수는 한 가지 일만 수행 (Modularity, Simplicity)
[ ] 코드는 트릭 없이 명확하게 작성 (Clarity)
[ ] 비즈니스 로직과 인프라 코드 분리 (Separation)
[ ] 실패 시 명확한 에러 메시지 반환 (Repair)
[ ] 불필요한 로그/출력 제거 (Silence)
[ ] API는 예측 가능하게 동작 (Least Surprise)
[ ] 과도한 추상화/최적화 금지 (Parsimony, Optimization)
```

### FastAPI 적용 예시

```python
# Modularity: 작은 함수로 분리
def validate_user(data: UserCreate) -> None:
    """사용자 데이터 검증만 수행"""
    if not data.email:
        raise ValueError("이메일 필수")

def create_user(db: Session, data: UserCreate) -> User:
    """사용자 생성만 수행"""
    validate_user(data)
    user = User(**data.dict())
    db.add(user)
    db.commit()
    return user

# Separation: 라우터와 서비스 분리
# routers/users.py - HTTP 처리만
@router.post("/users")
def create_user_endpoint(data: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, data)

# services/user_service.py - 비즈니스 로직만
def create_user(db: Session, data: UserCreate) -> User:
    ...

# Repair: 빠르고 명확한 실패
if not user:
    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

# Silence: 필요한 정보만 로깅
logger.info(f"User created: {user.id}")  # 필요한 정보만
# logger.debug(f"Full user data: {user.__dict__}")  # 개발 시에만

# Least Surprise: 일관된 응답 형식
return {"data": user, "message": "생성 완료"}
```

---

## Backend Configuration (CRITICAL)

### Allowed Hosts & CORS
백엔드 개발 시 다음 설정을 필수로 적용해야 한다:

1. **Allowed Hosts**: 모든 호스트 허용 (`*`)
2. **CORS Origin**: CORS origin 에러가 발생하지 않도록 설정

**FastAPI 설정 예시**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정 - 모든 origin 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)
```

**주의사항**:
- 개발 환경에서는 편의를 위해 모든 origin 허용
- 프로덕션 환경에서는 보안을 위해 특정 origin만 허용하도록 변경 필요

### Trailing Slash 통일 (CRITICAL)
**Frontend와 Backend에서 URL trailing slash를 반드시 통일해야 한다.**

`/api/users`와 `/api/users/`는 다른 URL로 처리될 수 있어 404 에러의 원인이 됨.

**규칙: Trailing Slash 없이 통일**

```
✅ 올바른 예시:
/api/v1/portfolio/summary
/api/v1/trades
/api/v1/stocks/AAPL

❌ 잘못된 예시:
/api/v1/portfolio/summary/
/api/v1/trades/
/api/v1/stocks/AAPL/
```

**Backend (FastAPI) 설정:**
```python
from fastapi import FastAPI

app = FastAPI()

# Trailing slash redirect 비활성화
app.router.redirect_slashes = False
```

**Frontend (Axios) 설정:**
```javascript
// API 호출 시 trailing slash 제거
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

// URL 정규화 (trailing slash 제거)
api.interceptors.request.use((config) => {
  if (config.url && config.url.endsWith('/')) {
    config.url = config.url.slice(0, -1);
  }
  return config;
});
```

**체크리스트:**
- [ ] Backend API 엔드포인트에 trailing slash 없음
- [ ] Frontend API 호출 URL에 trailing slash 없음
- [ ] SPEC.md API Design 섹션 URL 형식 통일

## Git
4) git commit message는 알아서 만들 것
   - 변경 내용 기반으로 명확한 메시지를 자동 생성
   - 커밋 메시지는 한국어로 작성한다.
   - 가능하면 Conventional Commits 사용
- 단, 환경 제약으로 git이 실패하면 사용자에게 원인/대안 커맨드를 안내한다.

---

## Debugging & Logging

### 로그 파일
- **Backend**: `backend/debug.log` - 모든 백엔드 동작 로그
- **Frontend**: `frontend/debug.log` - 모든 프론트엔드 동작 로그

### 핫리로드 시 로그 초기화 (CRITICAL)
**개발 서버 재시작(핫리로드) 시 기존 로그 파일을 삭제하고 새로 생성한다.**

이유: 분석해야 할 로그 범위를 줄여 디버깅 효율을 높이기 위함

**Backend (Python) - 서버 시작 시:**
```python
import os

# 서버 시작 시 기존 로그 삭제
LOG_FILE = 'debug.log'
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
    print(f"[LOG] 기존 로그 파일 삭제: {LOG_FILE}")
```

**Frontend (JavaScript) - 앱 시작 시:**
```javascript
// App.jsx 또는 main.jsx 최상단
if (import.meta.env.DEV) {
  localStorage.removeItem('debug_logs');
  console.log('[LOG] 기존 로그 초기화');
}
```

**dev.sh 스크립트에서 처리:**
```bash
# 개발 서버 시작 전 로그 파일 삭제
rm -f backend/debug.log frontend/debug.log
echo "[LOG] 로그 파일 초기화 완료"
```

### 로깅 필수 사항
1) **상세한 로그 기록**
   - 모든 API 요청/응답
   - 데이터베이스 쿼리
   - 사용자 인터랙션
   - 에러 및 예외 (스택 트레이스 포함)
   - 성능 메트릭 (처리 시간)

2) **로그 포맷**
   ```
   [타임스탬프] [레벨] [위치] 메시지 [데이터]
   ```

3) **로그 레벨**
   - DEBUG: 상세 디버깅 정보
   - INFO: 일반 정보
   - WARNING: 경고
   - ERROR: 에러
   - CRITICAL: 치명적 오류

### Backend (Python)
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
    handlers=[
        logging.FileHandler('debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 사용 예시
logger.info(f"API Request: GET /api/v1/addresses/{address}")
logger.error(f"Database error: {str(e)}", exc_info=True)
```

### Frontend (JavaScript)
```javascript
// 로그 유틸리티
const logger = {
  log: (level, message, data) => {
    const timestamp = new Date().toISOString();
    const logMsg = `[${timestamp}] [${level}] ${message}`;
    console.log(logMsg, data || '');

    // localStorage에 저장
    const logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
    logs.push({ timestamp, level, message, data });
    localStorage.setItem('debug_logs', JSON.stringify(logs.slice(-1000)));
  },
  debug: (msg, data) => logger.log('DEBUG', msg, data),
  info: (msg, data) => logger.log('INFO', msg, data),
  error: (msg, data) => logger.log('ERROR', msg, data)
};

// 사용 예시
logger.info('Fetching address data', { address });
logger.error('API request failed', { error: error.message });
```

### 로그 확인
```bash
# 실시간 로그 모니터링
tail -f backend/debug.log
tail -f frontend/debug.log

# 에러만 필터링
grep ERROR backend/debug.log
```

---

## 사용자에게 에러 표시 (필수)

### 원칙
**에러 발생 시 사용자에게 웹 UI에서 자세한 에러 메시지를 보여주어야 합니다.**

### Backend
```python
from fastapi import HTTPException

@app.get("/api/v1/addresses/{address}")
async def get_address(address: str):
    try:
        result = fetch_address(address)
        return result
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)

        # 개발: 상세 에러 정보 반환
        raise HTTPException(
            status_code=500,
            detail={
                "message": "주소 조회 중 오류 발생",
                "error": str(e),
                "type": type(e).__name__
            }
        )
```

### Frontend
```javascript
// 에러를 사용자에게 표시
const handleError = (error) => {
  // Toast 알림
  toast.error(
    <div>
      <div className="font-bold">{error.message}</div>
      {import.meta.env.DEV && error.details && (
        <div className="text-sm mt-1">{error.details}</div>
      )}
    </div>
  );

  logger.error('Error occurred', error);
};

// API 호출 시
try {
  const response = await fetch('/api/v1/addresses/...');
  if (!response.ok) {
    const errorData = await response.json();
    handleError(errorData.error);
  }
} catch (error) {
  handleError({ message: '네트워크 오류', details: error.message });
}
```

### 에러 표시 컴포넌트
```javascript
export const ErrorAlert = ({ error }) => (
  <div className="bg-red-50 border-l-4 border-red-500 p-4">
    <div className="font-bold">{error.message}</div>
    {import.meta.env.DEV && error.details && (
      <div className="text-sm mt-2">{error.details}</div>
    )}
  </div>
);
```

### 가이드라인
1. **명확한 메시지**: 무엇이 잘못되었는지 명확히 표시
2. **해결 방법 제시**: 사용자가 어떻게 해야 하는지 안내
3. **개발 환경 상세 정보**: 개발 시 스택 트레이스, 에러 타입 표시
4. **프로덕션 간소화**: 프로덕션에서는 민감 정보 숨김

**중요**: 문제 해결을 위해 충분히 상세한 로그를 남기고, **사용자에게도 명확한 에러 메시지를 표시**하는 것이 필수입니다.

---

## Claude Code 사용 가이드 (비개발자용)

이 템플릿은 비개발자도 Claude Code를 통해 프로젝트를 생성하고 배포할 수 있도록 설계되었습니다.

### 프로젝트 시작하기

**1. 프로젝트 생성**
```
"SPEC.md를 기반으로 프로젝트를 생성해줘"
```
- Claude Code가 frontend/, backend/ 폴더와 필요한 파일들을 자동 생성합니다.

**2. 의존성 설치**
```
"의존성 설치해줘" 또는 "./install.sh 실행해줘"
```

**3. 개발 서버 실행**
```
"개발 서버 실행해줘" 또는 "./dev.sh 실행해줘"
```
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API 문서: http://localhost:8000/docs

**4. 테스트 실행**
```
"테스트 실행해줘" 또는 "./test.sh 실행해줘"
```

### Railway 배포

**사전 준비** (최초 1회):
1. Railway 계정 생성: https://railway.app
2. Railway CLI 설치: `npm install -g @railway/cli`
3. Railway 로그인: `railway login`

**배포 요청**:
```
"Railway에 배포해줘"
```

Claude Code가 자동으로 수행하는 작업:
1. 테스트 실행 (통과 확인)
2. Git 커밋 (변경사항이 있는 경우)
3. `railway up` 실행 (Docker 빌드 및 배포)
4. 배포 URL 및 상태 확인

### 문제 해결

**배포 로그 확인**:
```
"배포 로그 확인해줘" 또는 "railway logs 실행해줘"
```

**배포 상태 확인**:
```
"배포 상태 확인해줘" 또는 "railway status 실행해줘"
```

**에러 발생 시**:
```
"에러 로그 확인해줘"
"문제 원인 분석해줘"
```

### SPEC.md 커스터마이징

새로운 프로젝트를 만들려면 SPEC.md 파일에서 다음을 수정하세요:

1. **프로젝트 이름/설명**: 1.1 Purpose 섹션
2. **데이터베이스 스키마**: 6. Database Schema 섹션
3. **API 엔드포인트**: 5. API Design 섹션
4. **UI 컴포넌트**: 8. Frontend Components 섹션

수정 후 Claude Code에게 "SPEC.md를 기반으로 프로젝트를 생성해줘"라고 요청하면 됩니다.

---

## 배포 설정

### Docker 기반 배포

이 프로젝트는 Dockerfile을 사용하여 Railway에 배포됩니다:

- **빌드**: Multi-stage Docker build
  - Stage 1: Node.js로 Frontend 빌드
  - Stage 2: Python으로 Backend 실행 + Frontend 정적 파일 서빙
- **헬스체크**: `/health` 엔드포인트
- **포트**: Railway가 자동으로 `PORT` 환경 변수 제공

### 환경 변수 (Railway 대시보드에서 설정)

**필수**:
- `DATABASE_URL`: PostgreSQL 연결 URL (Railway가 자동 제공)
- `SECRET_KEY`: 보안 키 (직접 설정)
- `ENVIRONMENT`: production

**선택**:
- `LOG_LEVEL`: INFO (기본값)
- `REDIS_URL`: Redis 연결 URL (캐싱 사용 시)
