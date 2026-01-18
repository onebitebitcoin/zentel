# Zettelkasten Mobile Memo Capture - Technical Specification (SPEC.md)

> **참고**: 이 프로젝트는 “젠텔카스텐(조텔카스텐) 메모 방식”을 **웹 기반**으로 직접 구현하는 프로젝트입니다.  
> 모바일 사용 비중이 높으므로 **Mobile-First + 빠른 캡처(Quick Capture)** 경험을 최우선으로 설계합니다.  
>
> 본 문서는 Claude Code / AI 코딩 에이전트가 개발을 진행할 때 **요구사항, 데이터 흐름, 스키마, API, UI 구조**를 오해 없이 구현하기 위한 기술 명세입니다.

---

## 0. Data Flow Definition (필수 - 프로젝트 시작 전 정의)

> **IMPORTANT**: 개발 전에 이 섹션을 먼저 확정해야 합니다.  
> 특히 “메모 타입(6종) → 임시 메모 저장 → 임시 메모 목록(최신순)” 흐름이 MVP의 핵심입니다.

### 0.1 Data Source (데이터 소스)

| 항목 | 내용 |
|------|------|
| **소스 타입** | User Input (사용자 직접 입력) |
| **소스 이름** | Quick Capture 입력 폼 |
| **접근 방법** | Web UI (모바일 친화) |
| **인증 필요** | MVP: 선택 (Anonymous Local / Optional Login) |
| **비용** | 없음 |
| **Rate Limit** | 해당 없음 |

> **향후 확장(선택)**  
> - 외부 문헌/링크(“fertilizer”)를 저장하기 위한 URL 메타데이터(OG 태그) 수집(서버에서 fetch)  
> - 음성 입력(모바일), 사진 첨부, 위치 태그(권한 기반)

---

### 0.2 Input (사용자 입력)

#### (MVP) Quick Capture 입력 항목

| 입력 항목 | 타입 | 예시 | 필수 여부 |
|-----------|------|------|----------|
| memo_type | Enum(6종) | `NEW_IDEA` | 필수 |
| content | String | “이 아이디어는 …” | 필수 |
| created_at | DateTime | 자동 생성 | 필수(자동) |
| context_meta | JSON | device, locale 등 | 선택(자동) |

#### Memo Type (6 categories)

| 코드 | 화면 표시(한글) | 의미 |
|------|------------------|------|
| `NEW_IDEA` | 새로운 아이디어 | 떠오른 새 아이디어를 즉시 기록합니다. |
| `NEW_GOAL` | 새로운 목표 | 달성하고 싶은 목표를 기록합니다. |
| `EVOLVED_THOUGHT` | 발전된 생각 | 강화/기각/수정 등 기존 생각을 발전시킨 기록입니다. |
| `CURIOSITY` | 호기심과 궁금증 | 더 알아보고 싶은 질문/호기심입니다. |
| `UNRESOLVED_PROBLEM` | 해결되지 않는 문제 | 막힌 문제, 해결되지 않은 이슈입니다. |
| `EMOTION` | 감정 | 감정 상태/원인/맥락을 기록합니다. |

---

### 0.3 Output (결과 출력)

| 출력 항목 | 형태 | 설명 |
|----------|------|------|
| Quick Capture 저장 결과 | Toast / Snackbar | “임시 메모가 저장되었습니다.” |
| 임시 메모(Inbox) 목록 | 카드 리스트 | **최신 날짜 순**으로 임시 메모를 표시합니다. |
| 카테고리 필터 | 칩/탭 | 6종 타입별 필터링을 제공합니다. |
| 임시 메모 상세 | Bottom Sheet/Detail | 내용 전체 보기, 수정/삭제, (향후) 영구 메모로 전환 버튼 |

---

### 0.4 Data Flow Diagram

```
┌─────────────┐        ┌──────────────────┐        ┌──────────────────┐
│   User      │        │  Frontend (Web)  │        │ Backend (API)    │
│ (Mobile)    │──────▶ │ Quick Capture UI │──────▶ │  FastAPI         │
└─────────────┘        └──────────────────┘        └──────────────────┘
                               │                            │
                               │                            ▼
                               │                     ┌──────────────┐
                               │                     │ Database      │
                               │                     │ (SQLite/Post) │
                               │                     └──────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │ Inbox List UI     │
                        │ (Latest First)    │
                        └──────────────────┘
```

---

### 0.5 Data Refresh (데이터 갱신 주기)

| 데이터 | 갱신 주기 | 방법 |
|--------|----------|------|
| 임시 메모 목록 | 화면 진입 시 / 저장 성공 후 | API 호출 또는 로컬 캐시 갱신 |
| 임시 메모 상세 | 요청 시 | On-demand |
| (선택) 오프라인 캐시 | 항상 | IndexedDB/Service Worker |

---

### 0.6 Data Access Checklist (개발 전 확인사항)

- [x] 데이터 소스는 사용자 입력입니다.
- [x] memo_type은 6종 Enum으로 고정입니다.
- [x] Quick Capture는 **한 화면에서 5초 이내 저장**을 목표로 합니다.
- [x] Inbox 목록은 **created_at 내림차순(최신순)**이 기본 정렬입니다.
- [ ] 오프라인 입력 지원(PWA)은 Phase 2에서 구현합니다(선택).

---

## 1. Project Overview

### 1.1 Purpose
이 프로젝트는 “언제 어디서든 떠오르면 즉시 적는다”라는 젠텔카스텐의 핵심 습관을 모바일 웹에서 구현합니다.  
첫 페이지(홈)는 곧바로 메모를 남길 수 있는 **Quick Capture**이며, 저장된 메모는 “임시 메모(Inbox)”에 쌓입니다.

### 1.2 Goals (MVP)
- 6가지 타입 중 하나를 선택하고 내용을 입력하여 **임시 메모 저장**
- 임시 메모 페이지에서 **최신순 리스트 조회**
- 최소한의 터치와 스크롤로 기록이 가능하도록 **Mobile-First UI** 적용

### 1.3 Target Users
- 모바일로 아이디어/목표/감정/질문을 빠르게 기록하고 싶은 사용자
- 메모를 나중에 정리(영구 메모화)하는 습관을 만들고 싶은 사용자

### 1.4 Key Use Cases (MVP)
- 홈에서 즉시 메모 작성 → 타입 선택 → 저장
- Inbox에서 최신 메모 확인
- (선택) 특정 타입만 필터링해서 보기

---

## 2. Domain Concepts (프로젝트 용어)

> 사용자의 기존 “rotten apple” 개념과 자연스럽게 연결되도록 용어를 정리합니다.

- **임시 메모(Temporary Memo)** = rotten apple  
  - 순간적으로 떠오른 재료를 빠르게 저장하는 영역입니다.
- **영구 메모(Permanent Note)** = apple *(Phase 2+)*  
  - 여러 임시 메모를 조합/정제하여 장기 지식으로 축적하는 영역입니다.
- **근거 문헌/기사(Fertilizer)** *(Phase 3+)*  
  - 영구 메모에 귀속되어 “근거/참고”로 연결 관리되는 자료입니다.
- **프로비넌스(Provenance)** *(Phase 2+)*  
  - 하나의 영구 메모가 어떤 임시 메모들의 조합으로 생성되었는지 출처를 기록합니다.

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                      Frontend (React)                         │
│  - Quick Capture (Home)                                       │
│  - Inbox (Temporary Memos)                                    │
│  - (Phase 2+) Note Composer (Permanent Note)                  │
└───────────────────────────────────────────────────────────────┘
                    ↕ HTTPS (REST)
┌───────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                        │
│  - Memo API (CRUD)                                            │
│  - Auth (optional)                                            │
│  - (Phase 2+) Note generation/provenance                      │
└───────────────────────────────────────────────────────────────┘
                    ↕
┌───────────────────────────────────────────────────────────────┐
│                 Database (SQLite → Postgres)                  │
│  - temp_memos                                                 │
│  - (Phase 2+) notes, note_provenance, note_links              │
└───────────────────────────────────────────────────────────────┘
```

### 3.2 Tech Stack (권장)
- **Frontend**: React + Vite + TypeScript + Tailwind
- **Backend**: FastAPI + Pydantic + SQLAlchemy
- **DB**: SQLite (dev) / Postgres (prod)
- **Deployment**: Railway / Fly.io / Render 중 택1
- **(선택) PWA**: Service Worker + IndexedDB로 오프라인 캡처 지원

---

## 4. Core Features & Functionality (MVP)

### 4.1 Quick Capture (Home, `/`)
**핵심 UX 원칙**
- 앱 진입 즉시 커서가 입력창에 포커스됩니다.
- 타입 선택은 “칩(Chip)” 형태로 6개를 한 화면에 노출합니다.
- 저장 버튼은 엄지로 누르기 쉬운 하단 고정(Fixed Bottom) 버튼을 사용합니다.
- 저장 성공 시 입력창을 비우고 토스트를 표시합니다.

**UI 구성(모바일 기준)**
- 상단: 앱 타이틀(작게) + “Inbox” 이동 아이콘
- 중단: 타입 칩 6개(2행 또는 가로 스크롤)
- 하단: 큰 멀티라인 텍스트 입력창
- 최하단: “저장” 버튼(고정)

### 4.2 Temporary Memo Inbox (`/inbox`)
- 기본 정렬: `created_at DESC`
- 카드에는 다음 정보를 표시합니다:
  - 타입(칩/배지)
  - 작성 시간(상대시간 + 상세는 절대시간)
  - 본문 미리보기(2~3줄)
- 상단에 타입 필터(전체 + 6종)
- 카드 탭 시 상세(Bottom Sheet 또는 Detail Page)

### 4.3 Basic Operations (MVP)
- 임시 메모 생성
- 임시 메모 목록 조회(최신순)
- 임시 메모 삭제
- (권장) 임시 메모 수정 *(초기에는 상세에서 edit 가능)*

---

## 5. API Design

### 5.1 REST Endpoints (MVP)

#### Temporary Memo
```
POST /api/v1/temp-memos
- 임시 메모 생성
- Body: { memo_type, content }
- Response: { id, memo_type, content, created_at }

GET /api/v1/temp-memos
- 임시 메모 목록 조회 (기본 최신순)
- Query: type(optional), limit(default=30), offset(default=0)
- Response: { items: [...], total, next_offset }

GET /api/v1/temp-memos/{id}
- 임시 메모 상세 조회

PATCH /api/v1/temp-memos/{id}
- 임시 메모 수정
- Body: { memo_type?, content? }

DELETE /api/v1/temp-memos/{id}
- 임시 메모 삭제
```

### 5.2 Request/Response Format
```json
{
  "status": "success",
  "data": {
    "id": "tm_01HZZ...",
    "memo_type": "NEW_IDEA",
    "content": "떠오른 생각...",
    "created_at": "2026-01-18T09:12:33+09:00"
  },
  "error": null,
  "metadata": {
    "timestamp": "2026-01-18T09:12:34+09:00",
    "version": "0.1.0"
  }
}
```

### 5.3 Error Codes
- `400`: 잘못된 입력(빈 content, 잘못된 memo_type)
- `404`: 리소스 없음
- `422`: Validation Error (Pydantic)
- `500`: 서버 오류

---

## 6. Database Schema (SQLite3)

> MVP는 임시 메모만 확정합니다.  
> Phase 2 이후에 notes/provenance/fertilizer를 추가합니다.

### 6.1 Tables

#### temp_memos
```sql
CREATE TABLE temp_memos (
  id TEXT PRIMARY KEY,                 -- 예: tm_ulid
  memo_type TEXT NOT NULL,             -- 6종 Enum 문자열
  content TEXT NOT NULL,
  created_at TEXT NOT NULL,            -- ISO8601 with timezone
  updated_at TEXT                      -- ISO8601
);

CREATE INDEX idx_temp_memos_created_at ON temp_memos(created_at DESC);
CREATE INDEX idx_temp_memos_type_created ON temp_memos(memo_type, created_at DESC);
```

### 6.2 (권장) ULID/UUID 정책
- 모바일에서 오프라인 저장까지 고려하면 **클라이언트 생성 ID(ULID)**가 유리합니다.
- 서버에서도 생성 가능하나, 향후 동기화 구조를 고려하여 ULID를 권장합니다.

---

## 7. Backend Implementation Notes (FastAPI)

### 7.1 Pydantic Schemas (예시)
```python
from enum import Enum
from pydantic import BaseModel, Field

class MemoType(str, Enum):
    NEW_IDEA = "NEW_IDEA"
    NEW_GOAL = "NEW_GOAL"
    EVOLVED_THOUGHT = "EVOLVED_THOUGHT"
    CURIOSITY = "CURIOSITY"
    UNRESOLVED_PROBLEM = "UNRESOLVED_PROBLEM"
    EMOTION = "EMOTION"

class TempMemoCreate(BaseModel):
    memo_type: MemoType
    content: str = Field(min_length=1, max_length=10000)

class TempMemoUpdate(BaseModel):
    memo_type: MemoType | None = None
    content: str | None = Field(default=None, min_length=1, max_length=10000)

class TempMemoOut(BaseModel):
    id: str
    memo_type: MemoType
    content: str
    created_at: str
    updated_at: str | None = None
```

### 7.2 Sorting Rule (중요)
- 목록 조회는 반드시 `ORDER BY created_at DESC`가 기본입니다.
- `type` 쿼리가 있으면 해당 타입만 필터링합니다.

---

## 8. Frontend UX / UI Guidelines (Mobile-First)

### 8.1 Mobile-First Rules
- 터치 타깃 최소 44x44px을 지킵니다.
- 저장 버튼은 하단 고정이며, 스크롤과 무관하게 항상 보입니다.
- 입력창은 화면 높이의 40~60%를 차지해도 됩니다(기록 우선).
- 홈 진입 시 키보드가 바로 올라오도록 포커스를 기본 적용합니다(단, iOS 정책상 일부 제한 가능).

### 8.2 Quick Capture Interaction
- 기본 선택 타입은 마지막으로 사용한 타입을 로컬에 저장하고 다음 진입 시 기본으로 선택합니다.
- 저장 시:
  1) 입력값 검증
  2) API 요청
  3) 성공 토스트
  4) content 초기화 + 타입 유지(사용성 우선)

### 8.3 Inbox List
- 상단 필터 탭: 전체 + 6종
- 무한 스크롤 또는 “더 보기” 버튼(모바일 성능 고려)
- 리스트 첫 로딩은 30개(limit=30)

---

## 9. Security & Privacy (기본 원칙)

- MVP에서 로그인 없이도 동작 가능하도록 설계할 수 있습니다(단일 사용자).
- 향후 멀티 디바이스/동기화가 필요하면 로그인/계정이 필요합니다.
- 감정(EMOTION) 메모가 민감할 수 있으므로:
  - 전송은 HTTPS만 허용합니다.
  - (선택) 로컬 암호화/잠금(PIN)은 Phase 3에서 다룹니다.

---

## 10. Development Phases

### Phase 1 (MVP): Quick Capture + Inbox
- [ ] React UI: Quick Capture (/)
- [ ] React UI: Inbox (/inbox) 최신순 리스트
- [ ] FastAPI: temp_memos CRUD
- [ ] SQLite 스키마 + 마이그레이션
- [ ] 모바일 UX(하단 고정 버튼, 입력 포커스, 토스트)

### Phase 2: 영구 메모(apple)로 발전 + 프로비넌스
- [ ] 임시 메모 다중 선택 → 영구 메모 생성
- [ ] 영구 메모에 “어떤 임시 메모를 조합했는지” provenance 기록
- [ ] 영구 메모 간 링크(양방향/백링크)

### Phase 3: Fertilizer(근거 문헌) 귀속 관리
- [ ] 영구 메모에 링크/논문/기사 첨부
- [ ] URL 메타데이터 수집(제목/출처/요약)
- [ ] fertilizer는 독립 노트가 아니라 특정 영구 메모에 귀속

### Phase 4: PWA 오프라인 캡처 + 동기화
- [ ] 오프라인에서도 저장(IndexedDB)
- [ ] 온라인 복귀 시 동기화
- [ ] 충돌 해결 정책 정의

---

## 11. Project Structure (권장)

```
zettel-web/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomeQuickCapture.tsx
│   │   │   └── Inbox.tsx
│   │   ├── components/
│   │   │   ├── MemoTypeChips.tsx
│   │   │   ├── BottomSaveButton.tsx
│   │   │   └── TempMemoCard.tsx
│   │   ├── api/
│   │   │   └── client.ts
│   │   └── App.tsx
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── temp_memos.py
│   │   ├── models/
│   │   │   └── temp_memo.py
│   │   ├── schemas/
│   │   │   └── temp_memo.py
│   │   ├── database.py
│   │   └── main.py
│   └── requirements.txt
│
├── SPEC.md
├── README.md
└── docker-compose.yml (optional)
```

---

## 12. Environment Variables

```bash
# .env.example

# Backend
DATABASE_URL=sqlite:///./zettel.db
LOG_LEVEL=INFO
ENVIRONMENT=development

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Zettel Mobile Memo
```

---

## 13. Testing Strategy

### 13.1 Backend
- temp_memos 생성/조회/정렬(최신순) 테스트
- memo_type Enum validation 테스트
- 빈 content 방지 테스트

### 13.2 Frontend
- Quick Capture 저장 플로우(E2E 권장: Playwright)
- Inbox 최신순 렌더링 스냅샷/통합 테스트
- 모바일 뷰포트(390x844) 기준 UI 테스트

---

## 14. Success Metrics (MVP)

- [ ] 홈 진입 후 **5초 이내 메모 저장** 가능
- [ ] 저장 성공률 > 99% (네트워크 정상 환경)
- [ ] Inbox 로딩 1초 내(로컬/일반 환경 기준)
- [ ] 모바일 사용성: 한 손 조작(하단 버튼/칩) 위주로 불편 최소화

---

**Document Version**: 0.1.0  
**Last Updated**: 2026-01-18 (Asia/Seoul)
