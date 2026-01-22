# Playwright 웹 컨텐츠 추출 샘플

Playwright를 사용하여 동적 웹사이트의 컨텐츠를 추출하는 샘플 구현입니다.

## 목적

- 정적 HTML 파서(httpx)로는 접근이 어려운 동적 웹사이트 스크래핑
- Twitter/X, Reddit 등 JavaScript로 렌더링되는 사이트 지원
- context_extractor.py에 통합하기 전 실현가능성 검토

## 설치

### 1. Playwright 패키지 설치

```bash
cd backend
source ../venv/bin/activate
pip install playwright
```

### 2. Chromium 브라우저 설치

```bash
playwright install chromium
```

## 사용법

### 기본 실행

```bash
cd samples
./run_sample.sh https://example.com
```

### Python 직접 실행

```bash
cd backend
source ../venv/bin/activate
cd ../samples
python playwright_scraper.py --url https://example.com
```

### 출력 형식

```json
{
  "url": "https://example.com",
  "og_metadata": {
    "title": "Example Domain",
    "image": "https://example.com/og-image.png",
    "description": "Example description"
  },
  "content": "전체 텍스트 내용...",
  "success": true,
  "elapsed_time": "2.5s"
}
```

## 테스트 시나리오

### 정적 사이트 테스트

```bash
./run_sample.sh https://example.com
./run_sample.sh https://python.org
```

### 동적 사이트 테스트

```bash
./run_sample.sh https://news.ycombinator.com
./run_sample.sh https://reddit.com
```

### 에러 처리 테스트

```bash
./run_sample.sh https://invalid-url-12345.com
./run_sample.sh https://httpstat.us/500
```

## 통합 계획

### Phase 1: 샘플 구현 (현재)

- samples/ 폴더에 독립 실행 가능한 스크립트
- 기본 기능 검증 및 성능 테스트

### Phase 2: context_extractor.py 통합

Fallback 패턴 적용:

```python
async def _fetch_url_content(self, url: str):
    # 1차: httpx 시도 (빠름)
    try:
        return await self._fetch_with_httpx(url)
    except Exception:
        pass

    # 2차: Playwright 시도 (동적 컨텐츠)
    return await self._fetch_with_playwright(url)
```

### Phase 3: 도메인별 최적화

- 동적 사이트 목록 관리 (twitter.com, reddit.com 등)
- 도메인별로 httpx/Playwright 선택
- 브라우저 인스턴스 재사용으로 성능 개선

## 제한사항

### 메모리 사용량

- Chromium 브라우저는 약 100-200MB 메모리 사용
- Railway 배포 시 메모리 제한(512MB)에 주의

### Railway 배포

프로덕션 배포 시 Dockerfile에 Playwright 브라우저 설치 추가 필요:

```dockerfile
RUN pip install playwright && playwright install chromium --with-deps
```

### 타임아웃

- 기본 타임아웃: 10초
- 느린 사이트는 타임아웃 발생 가능

### 에러 로깅

- 모든 에러는 상세히 로깅됨
- 실패 원인 파악을 위해 로그 확인 필수

## 성능 벤치마크

| 사이트 유형 | httpx | Playwright | 비고 |
|-------------|-------|------------|------|
| 정적 사이트 | 0.5초 | 2-3초 | httpx가 빠름 |
| 동적 사이트 | 실패 | 3-5초 | Playwright 필수 |
| SPA | 실패 | 4-6초 | Playwright 필수 |

## 문의

문제가 발생하면 backend/debug.log를 확인하세요.
