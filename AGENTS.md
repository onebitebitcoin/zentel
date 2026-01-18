# Agent Rules

## Language
- 모든 답변은 한국어로 작성한다.
- 코드/로그/에러 메시지는 원문을 유지하되, 설명은 한국어로 한다.

## Writing / UI Guidelines
1) 이모지를 사용하지 말고 아이콘을 사용할 것
   - 문서/설명에서 🎉 같은 이모지 금지
   - UI 구현에서는 아이콘 컴포넌트(예: lucide-react) 사용을 우선한다.

2) **중첩된 카드뷰는 사용하지 말 것 (CRITICAL)**
   - Card 안에 또 Card를 넣는 구조 금지
   - 필요하면 섹션 구분은 Divider, Header, Subsection, Background, Border 등으로 처리한다.
   - 레이아웃 깊이는 최대 2단계까지만 허용

3) **심플한 디자인 유지 (CRITICAL)**
   - 웹 UI에서 너무 많은 텍스트 설명을 표시하지 말 것
   - 긴 설명문, 상세 가이드, 도움말 텍스트는 최소화
   - 필요한 정보만 간결하게 표시
   - 상세 정보는 툴팁, 모달, 드롭다운 등으로 숨김 처리
   - "Less is more" 원칙 준수

   **좋은 예시**:
   ```jsx
   // ✅ 간결한 UI
   <div>
     <h2>주소 검색</h2>
     <Input placeholder="비트코인 주소 입력" />
     <Button>검색</Button>
   </div>

   // ❌ 너무 많은 설명
   <div>
     <h2>비트코인 주소 검색 기능</h2>
     <p>이 기능을 사용하면 비트코인 주소를 검색할 수 있습니다...</p>
     <p>검색 방법: 아래 입력란에 비트코인 주소를 입력하세요...</p>
     <p>주의사항: 올바른 형식의 주소를 입력해야 합니다...</p>
     <Input placeholder="비트코인 주소 입력" />
     <Button>검색</Button>
     <p>검색 버튼을 클릭하면 결과가 표시됩니다...</p>
   </div>
   ```

4) **모바일 친화적인 레이아웃으로 적용할 것 (CRITICAL)**
   - 기본을 모바일 우선(Mobile-first)로 설계한다.
   - 작은 화면에서 가독성(폰트/여백/줄바꿈)과 터치 타깃(버튼/링크)을 우선한다.
   - **모바일 좌우 padding은 최소한으로 설정** (예: `px-2`, `px-4`)
   - 항상 UI 업데이트 시 모바일에서 어떻게 보일지 고려

   **Tailwind CSS 예시**:
   ```jsx
   // ✅ 모바일 친화적인 padding
   <div className="px-2 sm:px-4 md:px-6 lg:px-8">
     {/* 모바일: px-2, 태블릿 이상: px-4+ */}
   </div>

   // ❌ 모바일에서 공간 낭비
   <div className="px-8 md:px-12 lg:px-16">
     {/* 모바일에서 너무 큰 padding */}
   </div>
   ```

   **사용자 요청 확인 (CRITICAL)**:
   - 사용자의 UI 요청이 **웹에만 한정되어 너무 디테일**하면 반드시 되물을 것
   - 예시 질문: **"이렇게 업데이트하면 모바일에서 레이아웃이 깨질 수 있는데 괜찮나요?"**
   - 모바일 호환성을 사용자에게 확인받고 진행
   - 웹 전용 디자인 요청 시 모바일 대안을 함께 제시

   **체크리스트**:
   - [ ] 모바일 화면에서 UI 깨지지 않는지 확인
   - [ ] 터치 타깃 크기 44x44px 이상
   - [ ] 가로 스크롤 발생하지 않는지 확인
   - [ ] 텍스트 크기 최소 14px 이상 (가독성)
   - [ ] 버튼/링크 간격 충분한지 확인

5) 시간/날짜는 항상 한국 시간(Asia/Seoul)을 기준으로 판단한다.

6) fallback 더미 값 주입으로 흐름을 숨기지 말 것
   - 디버깅을 어렵게 하므로 기본/더미 값으로 덮어쓰지 않는다.
   - 문제가 발생하면 에러 메시지를 명확히 노출한다.

7) 사용자 작업에는 성공/실패 메시지를 항상 노출할 것
   - 저장/추가/삭제/새로고침 등 주요 액션의 결과를 명확히 표시한다.

## Workflow (필수)
- 변경 사항이 생기면 아래 순서로 마무리한다.
  1) **Lint 체크 (테스트 전 필수)**
     - Frontend (React): `npm run lint` (ESLint)
     - Backend (FastAPI): `ruff check .` 또는 `flake8`
     - 에러가 있으면 수정 후 다시 체크
  2) 테스트 실행(프로젝트 표준 커맨드 사용)
  3) **테스트 결과를 테이블 형태로 출력 (필수)**
  4) PASS/FAIL 확인 후, FAIL이면 수정 → 재테스트 반복
  5) **PASS면 반드시 `git add` → `git commit` 수행 (절대 누락 금지)**
  6) `git push`는 사용자가 명시적으로 요청할 때만 수행한다.

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

## Database & API Synchronization (CRITICAL)
**스키마와 API는 항상 함께 업데이트되어야 한다.**

처음에 만든 스키마와 API가 다른 상태에서 스키마가 업데이트되면 API는 업데이트되지 않기 때문에, 반드시 CRUD 기능에서는 스키마 업데이트와 API 업데이트를 같이 취급해야 한다.

### 원칙
- 데이터베이스 스키마가 변경되면 반드시 관련 API도 함께 업데이트해야 함
- CRUD 기능 개발/수정 시 스키마와 API를 항상 같이 취급할 것
- 스키마만 업데이트하고 API를 업데이트하지 않으면 불일치가 발생하여 런타임 에러 발생

### 예시
- **스키마에 새 필드 추가** → API response model (Pydantic)에도 필드 추가
- **스키마에서 필드 제거** → API request/response model에서도 해당 필드 제거
- **스키마 필드 타입 변경** → API validation/serialization 로직도 변경
- **필드명 변경** → API 모델, 쿼리 로직, 문서 모두 변경

### 체크리스트
스키마 변경 시 반드시 확인할 항목:
1. [ ] 영향받는 모든 API 엔드포인트 확인
2. [ ] Pydantic 모델 (request/response schemas) 업데이트
3. [ ] SQLAlchemy 모델과 Pydantic 모델 일치 확인
4. [ ] API 문서 (Swagger/OpenAPI) 자동 반영 확인
5. [ ] 관련 테스트 코드 업데이트
6. [ ] 마이그레이션 스크립트 작성 (필요시)

### 나쁜 예시
```python
# ❌ 스키마만 변경하고 API는 업데이트하지 않음
# models.py
class Address(Base):
    address = Column(String)
    balance = Column(Float)
    cluster_id = Column(String)
    tx_count = Column(Integer)  # 새로 추가

# schemas.py (업데이트 안 함!)
class AddressResponse(BaseModel):
    address: str
    balance: float
    cluster_id: str
    # tx_count 누락! → API 응답에 포함되지 않음
```

### 좋은 예시
```python
# ✅ 스키마와 API를 함께 업데이트
# models.py
class Address(Base):
    address = Column(String)
    balance = Column(Float)
    cluster_id = Column(String)
    tx_count = Column(Integer)  # 새로 추가

# schemas.py (함께 업데이트!)
class AddressResponse(BaseModel):
    address: str
    balance: float
    cluster_id: str
    tx_count: int  # 추가됨 ✓
```

---

## Backend Development - 12-Factor App (CRITICAL)

**Backend 개발 시 반드시 12-Factor App 방법론을 따라야 한다.**

12-Factor App은 확장 가능하고 유지보수가 쉬운 SaaS 애플리케이션을 구축하기 위한 방법론이다.
참고: https://12factor.net/

### 12가지 원칙

| # | 원칙 | 설명 | 적용 예시 |
|---|------|------|----------|
| 1 | **Codebase** | 버전 관리되는 하나의 코드베이스, 여러 배포 | Git으로 관리, dev/staging/prod 환경 분리 |
| 2 | **Dependencies** | 의존성을 명시적으로 선언하고 격리 | `requirements.txt`, `pyproject.toml` 사용 |
| 3 | **Config** | 설정을 환경 변수로 분리 | `.env` 파일, `os.getenv()` 사용 |
| 4 | **Backing Services** | 백엔드 서비스를 연결된 리소스로 취급 | DB, Redis, S3를 URL로 연결 |
| 5 | **Build, Release, Run** | 빌드/릴리스/실행 단계 엄격히 분리 | Docker 빌드 → 이미지 태깅 → 컨테이너 실행 |
| 6 | **Processes** | 무상태(Stateless) 프로세스로 실행 | 세션은 Redis/DB에 저장, 로컬 파일 의존 금지 |
| 7 | **Port Binding** | 포트 바인딩으로 서비스 노출 | `uvicorn app:app --port $PORT` |
| 8 | **Concurrency** | 프로세스 모델로 수평 확장 | 워커 수 조절, 로드밸런서 사용 |
| 9 | **Disposability** | 빠른 시작/종료로 견고성 확보 | graceful shutdown, 시그널 핸들링 |
| 10 | **Dev/Prod Parity** | 개발/스테이징/프로덕션 환경 동일하게 유지 | Docker로 환경 통일, 같은 DB 종류 사용 |
| 11 | **Logs** | 로그를 이벤트 스트림으로 취급 | stdout 출력, 로그 수집기가 처리 |
| 12 | **Admin Processes** | 관리 작업을 일회성 프로세스로 실행 | 마이그레이션, 스크립트를 별도 명령으로 |

### 필수 체크리스트

```
[ ] 모든 설정은 환경 변수로 관리 (하드코딩 금지)
[ ] 의존성은 requirements.txt 또는 pyproject.toml에 명시
[ ] 프로세스는 무상태로 유지 (로컬 파일 시스템 의존 금지)
[ ] 로그는 stdout으로 출력 (파일 직접 쓰기는 개발 환경만)
[ ] graceful shutdown 구현
[ ] 개발/프로덕션 환경 차이 최소화
```

### FastAPI 적용 예시

```python
import os
from fastapi import FastAPI

# Config: 환경 변수로 설정 관리
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

# Port Binding: 환경 변수로 포트 설정
PORT = int(os.getenv("PORT", 8000))

# Processes: 무상태 유지
# ❌ 잘못된 예시 - 로컬 파일에 상태 저장
# user_sessions = {}  # 메모리에 세션 저장

# ✅ 올바른 예시 - 외부 서비스 사용
# from redis import Redis
# redis_client = Redis.from_url(REDIS_URL)
```

---

## Backend Configuration (CRITICAL)

백엔드 개발 시 반드시 적용해야 할 설정들입니다.

### Allowed Hosts & CORS

**필수 설정**:
1. **Allowed Hosts**: 모든 호스트 허용 (`*`)
2. **CORS Origin**: CORS origin 에러가 발생하지 않도록 설정

이는 개발 환경에서 프론트엔드와 백엔드 간의 통신 문제를 방지하기 위함입니다.

### FastAPI 설정 방법

**main.py 또는 app/__init__.py**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Bitcoin Cracker API",
    description="Bitcoin 블록체인 분석 API",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 모든 origin 허용 (개발 환경)
    allow_credentials=True,     # 쿠키 포함 요청 허용
    allow_methods=["*"],        # 모든 HTTP 메서드 허용 (GET, POST, PUT, DELETE 등)
    allow_headers=["*"],        # 모든 헤더 허용
)
```

### 환경별 설정 예시

더 나은 방법은 환경 변수를 사용하여 개발/프로덕션 환경을 구분하는 것입니다:

```python
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 환경 설정
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

app = FastAPI()

# 환경에 따른 CORS 설정
if ENVIRONMENT == "development":
    # 개발 환경: 모든 origin 허용
    origins = ["*"]
else:
    # 프로덕션: 특정 origin만 허용
    origins = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 확인 방법

CORS가 올바르게 설정되었는지 확인:
```bash
# 브라우저 개발자 도구 콘솔에서 확인
# CORS 에러가 없어야 함:
# ❌ "Access to fetch at '...' from origin '...' has been blocked by CORS policy"
# ✅ 정상적으로 API 요청이 성공함
```

### 주의사항

- **개발 환경**: 편의를 위해 모든 origin 허용 (`allow_origins=["*"]`)
- **프로덕션 환경**: 보안을 위해 특정 origin만 허용 (도메인 명시)
- **allow_credentials=True** 사용 시 `allow_origins=["*"]`는 보안상 권장되지 않으나, 개발 환경에서는 편의성을 우선

---

## Git Rules
4) git commit message는 알아서 만들 것
   - 변경 내용 기반으로 명확하고 간결한 메시지를 자동 생성한다.
   - 커밋 메시지는 한국어로 작성한다.
   - 가능하면 Conventional Commits 형식(예: `fix: ...`, `feat: ...`, `refactor: ...`)을 따른다.
- 단, 실행 환경 제약(샌드박스 등)으로 git이 실패하면:
  - 실패 원인을 사용자에게 알리고, 사용자가 로컬 터미널에서 실행할 수 있도록 필요한 명령을 제시한다.

---

## Debugging & Logging (중요)

### 로그 파일 위치
- **Backend**: `backend/debug.log`
- **Frontend**: `frontend/debug.log`

### 로깅 원칙
1) **상세한 로그 기록 필수**
   - 모든 주요 동작에 대해 상세한 로그를 남긴다.
   - 디버깅이 쉽도록 충분한 컨텍스트 정보를 포함한다.

2) **로그 레벨**
   - `DEBUG`: 상세한 디버깅 정보 (개발 단계)
   - `INFO`: 일반적인 정보 (주요 동작 시작/완료)
   - `WARNING`: 경고 (잠재적 문제)
   - `ERROR`: 에러 (예외 발생, 실패)
   - `CRITICAL`: 치명적 오류 (서비스 중단 수준)

3) **로그 포맷**
   ```
   [YYYY-MM-DD HH:MM:SS] [LEVEL] [파일명:라인] 메시지
   ```

### Backend 로깅 (Python)

**설정 예시** (`backend/app/logger.py`):
```python
import logging
from datetime import datetime

# 로거 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
    handlers=[
        logging.FileHandler('debug.log', encoding='utf-8'),
        logging.StreamHandler()  # 콘솔에도 출력
    ]
)

logger = logging.getLogger(__name__)
```

**로깅해야 할 항목**:
- API 요청/응답 (엔드포인트, 파라미터, 상태 코드)
- 데이터베이스 쿼리 (SQL, 실행 시간)
- Bitcoin RPC 호출 (메서드, 파라미터, 응답)
- 클러스터링 작업 (시작/종료, 처리된 데이터 수)
- 예외 및 에러 (스택 트레이스 포함)
- 성능 메트릭 (처리 시간, 메모리 사용량)

**예시**:
```python
# API 요청 로깅
logger.info(f"API Request: GET /api/v1/addresses/{address}")

# 데이터베이스 쿼리
logger.debug(f"DB Query: SELECT * FROM addresses WHERE cluster_id = {cluster_id}")

# 에러 로깅
try:
    result = some_function()
except Exception as e:
    logger.error(f"Error in some_function: {str(e)}", exc_info=True)

# 성능 로깅
import time
start = time.time()
process_data()
logger.info(f"process_data completed in {time.time() - start:.2f}s")
```

### Frontend 로깅 (JavaScript/TypeScript)

**설정 예시** (`frontend/src/utils/logger.js`):
```javascript
const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARNING: 2,
  ERROR: 3,
  CRITICAL: 4
};

class Logger {
  constructor() {
    this.logFile = 'debug.log';
    this.minLevel = LOG_LEVELS.DEBUG;
  }

  formatMessage(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const caller = new Error().stack.split('\n')[3].trim();
    let log = `[${timestamp}] [${level}] ${message}`;
    if (data) {
      log += ` | Data: ${JSON.stringify(data)}`;
    }
    return log;
  }

  async writeLog(level, message, data = null) {
    const logMessage = this.formatMessage(level, message, data);

    // 콘솔 출력
    console.log(logMessage);

    // 파일에 저장 (개발 환경)
    if (import.meta.env.DEV) {
      // Node.js fs 또는 브라우저 localStorage 사용
      const logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
      logs.push(logMessage);
      localStorage.setItem('debug_logs', JSON.stringify(logs));
    }
  }

  debug(message, data) { this.writeLog('DEBUG', message, data); }
  info(message, data) { this.writeLog('INFO', message, data); }
  warning(message, data) { this.writeLog('WARNING', message, data); }
  error(message, data) { this.writeLog('ERROR', message, data); }
  critical(message, data) { this.writeLog('CRITICAL', message, data); }
}

export const logger = new Logger();
```

**로깅해야 할 항목**:
- 페이지 로드 및 컴포넌트 마운트
- API 호출 (URL, 파라미터, 응답 시간, 상태)
- 사용자 인터랙션 (버튼 클릭, 입력, 검색)
- 상태 변경 (Redux/Context 상태 업데이트)
- 렌더링 성능 (컴포넌트 렌더링 시간)
- 에러 및 예외 (네트워크 오류, 파싱 오류)
- 브라우저 정보 (User Agent, 화면 크기)

**예시**:
```javascript
import { logger } from '@/utils/logger';

// API 호출 로깅
const fetchAddress = async (address) => {
  logger.info(`Fetching address data: ${address}`);

  try {
    const start = performance.now();
    const response = await fetch(`/api/v1/addresses/${address}`);
    const duration = performance.now() - start;

    logger.info(`API response received in ${duration.toFixed(2)}ms`, {
      status: response.status,
      address
    });

    return await response.json();
  } catch (error) {
    logger.error(`Failed to fetch address: ${address}`, { error: error.message });
    throw error;
  }
};

// 사용자 인터랙션 로깅
const handleSearchClick = () => {
  logger.debug('Search button clicked', { query: searchQuery });
  performSearch(searchQuery);
};

// 상태 변경 로깅
useEffect(() => {
  logger.debug('Cluster data updated', {
    clusterCount: clusters.length,
    totalAddresses: clusters.reduce((sum, c) => sum + c.addressCount, 0)
  });
}, [clusters]);
```

### 로그 파일 관리

1) **로그 로테이션**
   - 로그 파일이 너무 커지지 않도록 주기적으로 순환
   - 예: `debug.log`, `debug.log.1`, `debug.log.2`

2) **.gitignore에 추가**
   ```
   backend/debug.log
   backend/debug.log.*
   frontend/debug.log
   frontend/debug.log.*
   ```

3) **개발 시 로그 확인**
   ```bash
   # 실시간 로그 확인
   tail -f backend/debug.log
   tail -f frontend/debug.log

   # 에러만 필터링
   grep ERROR backend/debug.log
   ```

### 프로덕션 환경

- 프로덕션에서는 `INFO` 레벨 이상만 로깅
- 민감한 정보 (비밀번호, 토큰) 로깅 금지
- 로그 집계 시스템 사용 (Sentry, LogRocket 등)

---

## 사용자에게 에러 표시 (CRITICAL)

### 기본 원칙
**에러 발생 시 사용자에게 자세한 에러 메시지를 웹 UI에 표시해야 합니다.**

이는 디버깅을 위해 필수적입니다:
- 개발자가 문제를 빠르게 파악할 수 있음
- 사용자가 문제를 정확히 보고할 수 있음
- 로그만으로는 재현하기 어려운 문제를 추적 가능

### Backend에서 에러 응답

**에러 발생 시 상세 정보를 포함한 JSON 응답**:

```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """모든 예외를 캐치하여 상세 정보 반환"""

    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    # 개발 환경: 상세 에러 정보 포함
    if settings.ENVIRONMENT == "development":
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.now().isoformat()
                }
            }
        )

    # 프로덕션: 일반적인 메시지
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "type": "ServerError",
                "message": "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "timestamp": datetime.now().isoformat()
            }
        }
    )

# 특정 엔드포인트에서 에러 처리
@app.get("/api/v1/addresses/{address}")
async def get_address(address: str):
    try:
        result = fetch_address_from_db(address)
        if not result:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"주소를 찾을 수 없습니다: {address}",
                    "address": address,
                    "suggestion": "주소가 올바른지 확인해주세요."
                }
            )
        return result

    except ValueError as e:
        logger.error(f"Invalid address format: {address}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail={
                "message": "잘못된 주소 형식입니다.",
                "address": address,
                "error": str(e)
            }
        )

    except Exception as e:
        logger.error(f"Error fetching address: {address}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": "주소 조회 중 오류가 발생했습니다.",
                "error": str(e),
                "type": type(e).__name__
            }
        )
```

### Frontend에서 에러 표시

**1. 에러 토스트/알림 표시**:

```javascript
import { toast } from 'react-hot-toast';  // 또는 다른 알림 라이브러리

const fetchAddress = async (address) => {
  try {
    const response = await fetch(`/api/v1/addresses/${address}`);

    if (!response.ok) {
      const errorData = await response.json();

      // 사용자에게 에러 표시
      showErrorToUser(errorData);

      throw new Error(errorData.error?.message || 'API 요청 실패');
    }

    return await response.json();

  } catch (error) {
    logger.error('Failed to fetch address', { address, error: error.message });

    // 네트워크 에러 등
    showErrorToUser({
      error: {
        message: '네트워크 오류가 발생했습니다.',
        details: error.message
      }
    });

    throw error;
  }
};

// 에러를 사용자에게 표시하는 함수
const showErrorToUser = (errorData) => {
  const { error } = errorData;

  // Toast 알림으로 표시
  toast.error(
    <div>
      <div className="font-bold">{error.message}</div>
      {error.details && (
        <div className="text-sm mt-1 opacity-80">{error.details}</div>
      )}
      {error.type && (
        <div className="text-xs mt-1 opacity-60">타입: {error.type}</div>
      )}
    </div>,
    {
      duration: 5000,
      position: 'top-right'
    }
  );

  // 또는 모달로 표시
  // openErrorModal(error);
};
```

**2. 전역 에러 바운더리**:

```javascript
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    logger.error('React Error Boundary caught error', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack
    });

    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-red-50">
          <div className="max-w-2xl p-8 bg-white rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold text-red-600 mb-4">
              오류가 발생했습니다
            </h2>

            <div className="mb-4">
              <p className="text-gray-700 mb-2">
                {this.state.error?.message || '알 수 없는 오류'}
              </p>
            </div>

            {/* 개발 환경에서만 상세 정보 표시 */}
            {import.meta.env.DEV && (
              <details className="mt-4">
                <summary className="cursor-pointer text-sm text-gray-600">
                  상세 정보 보기
                </summary>
                <pre className="mt-2 p-4 bg-gray-100 rounded text-xs overflow-auto">
                  {this.state.error?.stack}
                  {'\n\n'}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}

            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              페이지 새로고침
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// App.jsx에서 사용
function App() {
  return (
    <ErrorBoundary>
      <YourApp />
    </ErrorBoundary>
  );
}
```

**3. 에러 표시 컴포넌트**:

```javascript
// ErrorAlert.jsx
export const ErrorAlert = ({ error, onClose }) => {
  if (!error) return null;

  return (
    <div className="fixed top-4 right-4 max-w-md bg-red-50 border-l-4 border-red-500 p-4 shadow-lg rounded">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {/* Lucide React 아이콘 사용 */}
          <AlertCircle className="h-5 w-5 text-red-500" />
        </div>

        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">
            {error.message || '오류 발생'}
          </h3>

          {error.details && (
            <p className="mt-2 text-sm text-red-700">
              {error.details}
            </p>
          )}

          {import.meta.env.DEV && error.type && (
            <p className="mt-1 text-xs text-red-600">
              타입: {error.type}
            </p>
          )}

          {import.meta.env.DEV && error.traceback && (
            <details className="mt-2">
              <summary className="text-xs text-red-600 cursor-pointer">
                스택 트레이스
              </summary>
              <pre className="mt-1 text-xs bg-red-100 p-2 rounded overflow-auto max-h-40">
                {error.traceback}
              </pre>
            </details>
          )}
        </div>

        <button
          onClick={onClose}
          className="ml-3 flex-shrink-0 text-red-500 hover:text-red-700"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

// 사용 예시
function MyComponent() {
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    try {
      await apiCall();
    } catch (err) {
      setError(err.response?.data?.error || { message: err.message });
    }
  };

  return (
    <>
      <ErrorAlert error={error} onClose={() => setError(null)} />
      {/* 나머지 UI */}
    </>
  );
}
```

### 에러 메시지 가이드라인

1. **명확성**: 무엇이 잘못되었는지 명확히 표시
   ```
   ✅ "주소 형식이 올바르지 않습니다: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
   ❌ "오류 발생"
   ```

2. **해결 방법 제시**: 사용자가 어떻게 해야 하는지 안내
   ```
   ✅ "비트코인 주소를 찾을 수 없습니다. 주소를 다시 확인하거나 데이터 동기화를 기다려주세요."
   ❌ "404 Not Found"
   ```

3. **개발 환경에서만 상세 정보**:
   - 개발: 스택 트레이스, 에러 타입, 원본 메시지
   - 프로덕션: 일반적인 메시지만

4. **다국어 지원 고려**:
   ```javascript
   const errorMessages = {
     NETWORK_ERROR: "네트워크 연결을 확인해주세요.",
     NOT_FOUND: "요청한 리소스를 찾을 수 없습니다.",
     // ...
   };
   ```

### 체크리스트

- [ ] Backend에서 모든 예외에 대해 상세한 에러 응답 반환
- [ ] Frontend에서 API 에러를 사용자에게 표시
- [ ] 전역 에러 바운더리 구현
- [ ] 개발 환경에서 스택 트레이스 표시
- [ ] 프로덕션에서 민감 정보 숨김
- [ ] 에러 로그와 UI 표시 모두 수행

---

**중요**: 디버깅을 위해 충분히 상세한 로그를 남기는 것은 필수입니다. 로그가 부족하면 문제 해결이 어려우므로 항상 주요 동작에 대한 로그를 기록하세요. **또한 에러 발생 시 사용자에게도 명확한 에러 메시지를 보여주어야 합니다.**
