# 빠른 시작 가이드

비개발자도 5분 안에 프로젝트를 시작할 수 있는 가이드입니다.

---

## 1. 사전 준비

### 필수 도구 설치

**Node.js** (v18 이상)
```bash
# macOS
brew install node

# Windows
# https://nodejs.org 에서 다운로드
```

**Python** (v3.10 이상)
```bash
# macOS
brew install python@3.11

# Windows
# https://python.org 에서 다운로드
```

**Claude Code**
```bash
npm install -g @anthropic-ai/claude-code
```

---

## 2. 프로젝트 시작하기

### Step 1: Claude Code 실행

프로젝트 폴더에서 터미널을 열고:
```bash
claude
```

### Step 2: 프로젝트 생성 요청

Claude Code에게 말하기:
```
"SPEC.md를 기반으로 프로젝트를 생성해줘"
```

Claude Code가 자동으로:
- frontend/ 폴더 생성 (React 앱)
- backend/ 폴더 생성 (FastAPI 앱)
- 필요한 설정 파일들 생성

### Step 3: 의존성 설치

```
"의존성 설치해줘"
```

### Step 4: 개발 서버 실행

```
"개발 서버 실행해줘"
```

브라우저에서 확인:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API 문서: http://localhost:8000/docs

---

## 3. 나만의 프로젝트 만들기

### SPEC.md 수정하기

`SPEC.md` 파일을 열어서 다음을 변경하세요:

1. **프로젝트 이름**: "Bitcoin Cracker" → 원하는 이름
2. **프로젝트 설명**: 1.1 Purpose 섹션
3. **데이터베이스 테이블**: 6. Database Schema 섹션
4. **API 엔드포인트**: 5. API Design 섹션

### 예시: 할 일 관리 앱으로 변경

SPEC.md에서 Database Schema 섹션을 다음과 같이 변경:

```sql
CREATE TABLE todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    completed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

그리고 Claude Code에게:
```
"SPEC.md를 기반으로 프로젝트를 새로 생성해줘"
```

---

## 4. Railway 배포

### 사전 준비 (최초 1회)

1. Railway 계정 생성: https://railway.app

2. Railway CLI 설치:
```bash
npm install -g @railway/cli
```

3. Railway 로그인:
```bash
railway login
```

### 배포하기

Claude Code에게:
```
"Railway에 배포해줘"
```

Claude Code가 자동으로:
1. 테스트 실행
2. Git 커밋
3. Docker 이미지 빌드
4. Railway에 배포
5. 배포 URL 제공

---

## 5. 자주 사용하는 명령어

| 작업 | Claude Code에게 말하기 |
|------|----------------------|
| 프로젝트 생성 | "SPEC.md를 기반으로 프로젝트를 생성해줘" |
| 의존성 설치 | "의존성 설치해줘" |
| 개발 서버 실행 | "개발 서버 실행해줘" |
| 테스트 실행 | "테스트 실행해줘" |
| Railway 배포 | "Railway에 배포해줘" |
| 배포 로그 확인 | "배포 로그 확인해줘" |
| 에러 해결 | "에러 원인 분석해줘" |

---

## 6. 문제 해결

### "command not found" 에러

Node.js나 Python이 설치되지 않았습니다:
```bash
# 설치 확인
node --version
python3 --version
```

### Railway 배포 실패

```
"배포 로그 확인해줘"
```

로그를 보고 Claude Code에게:
```
"이 에러 해결해줘: [에러 메시지]"
```

### 개발 서버가 실행되지 않음

```
"에러 로그 확인해줘"
```

---

## 도움이 필요하면?

Claude Code에게 물어보세요:
```
"[문제 상황] 어떻게 해결해?"
```

예시:
- "API 엔드포인트 추가하는 방법 알려줘"
- "데이터베이스 테이블 추가하고 싶어"
- "로그인 기능 추가해줘"
