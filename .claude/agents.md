# Agent Rules

이 문서는 AI 에이전트(Claude 등)가 이 프로젝트에서 작업할 때 따라야 하는 규칙을 정의합니다.

## Language
- 모든 답변은 한국어로 작성
- 코드/로그/에러 메시지는 원문 유지, 설명은 한국어

---

## 기능 추가 시 테스트 자동 작성 (CRITICAL)

**새로운 기능을 추가하면 반드시 해당 기능의 테스트 코드도 함께 작성해야 한다.**

### Backend 기능 추가 시
- `backend/tests/` 폴더에 테스트 추가
- 해당 API 엔드포인트의 성공/실패 케이스 테스트
- 엣지 케이스 및 유효성 검증 테스트

**테스트 파일 위치**: `backend/tests/test_*.py`

**테스트 실행 명령**:
```bash
cd backend && python3 -m pytest tests/ -v --tb=short
```

### Frontend 기능 추가 시
- `frontend/src/**/*.test.ts` 파일에 테스트 추가
- 컴포넌트/훅/유틸리티 함수 테스트

**테스트 파일 위치**: `frontend/src/**/*.test.ts`, `frontend/src/**/*.test.tsx`

**테스트 실행 명령**:
```bash
cd frontend && npm test
```

### 테스트 시나리오 필수 항목

| 시나리오 | 설명 | 예시 |
|----------|------|------|
| Happy Path | 정상 동작 케이스 | 유효한 데이터로 생성 성공 |
| Error Case | 에러 발생 케이스 | 잘못된 입력, 권한 없음, 404 |
| Edge Case | 경계값 케이스 | 빈 값, null, 최대/최소값 |
| Combination | 조합 케이스 | 필터 + 검색, 페이지네이션 |

---

## 테스트 요청 처리

사용자가 다음과 같이 요청하면 해당 테스트를 실행한다:

| 사용자 요청 | 실행 명령 |
|-------------|-----------|
| "테스트 실행해줘" | Frontend + Backend 모두 |
| "frontend 테스트" | `cd frontend && npm run lint && npm test` |
| "backend 테스트" | `cd backend && python3 -m pytest tests/ -v --tb=short` |
| "린트 체크" | Frontend: `npm run lint`, Backend: `ruff check .` |

---

## 테스트 결과 출력 형식 (필수)

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

---

## Workflow

1. **기능 개발 완료**
2. **테스트 코드 작성** (해당 기능의 테스트 시나리오)
3. **Lint 체크**
4. **테스트 실행** → PASS/FAIL 확인
5. **테스트 결과 테이블 출력**
6. FAIL이면 수정 후 재테스트
7. **PASS면 반드시 git commit** (절대 누락 금지)

---

## 테스트 작성 예시

### Backend (FastAPI + pytest)

```python
# backend/tests/test_feature.py

def test_feature_success(authenticated_client):
    """기능 정상 동작 테스트"""
    response = authenticated_client.post(
        "/api/v1/feature",
        json={"field": "value"},
    )
    assert response.status_code == 201
    assert "id" in response.json()


def test_feature_invalid_input(authenticated_client):
    """잘못된 입력 테스트"""
    response = authenticated_client.post(
        "/api/v1/feature",
        json={"field": ""},  # 빈 값
    )
    assert response.status_code == 422


def test_feature_not_found(authenticated_client):
    """존재하지 않는 리소스 테스트"""
    response = authenticated_client.get("/api/v1/feature/nonexistent")
    assert response.status_code == 404


def test_feature_unauthorized(client):
    """인증 없이 접근 테스트"""
    response = client.get("/api/v1/feature")
    assert response.status_code == 401
```

### Frontend (Vitest/Jest)

```typescript
// frontend/src/utils/feature.test.ts

import { describe, it, expect } from 'vitest';
import { featureFunction } from './feature';

describe('featureFunction', () => {
  it('정상적인 입력 처리', () => {
    const result = featureFunction('valid input');
    expect(result).toBe('expected output');
  });

  it('빈 입력 처리', () => {
    const result = featureFunction('');
    expect(result).toBeNull();
  });

  it('에러 케이스 처리', () => {
    expect(() => featureFunction(null)).toThrow();
  });
});
```

---

## 참고

- CLAUDE.md의 전체 규칙도 함께 따를 것
- Unix Philosophy 원칙 준수 (Modularity, Clarity, Repair 등)
- 테스트 없이 기능만 추가하면 안 됨
