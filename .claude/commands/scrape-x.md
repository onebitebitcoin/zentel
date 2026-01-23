# X 스크래핑 테스트

X(Twitter) URL을 스크래핑하고 결과를 확인하는 skill입니다.

## 입력
URL: $ARGUMENTS

## 작업 지시

1. **URL 검증**: 입력된 URL이 X/Twitter URL인지 확인
   - `twitter.com`, `x.com` 도메인 확인
   - `/status/` 패턴으로 트윗 URL 확인

2. **스크래핑 테스트 실행**:
   ```bash
   cd /Users/nsw/Desktop/dev/aicoding-tests/zentel/backend
   python -m samples.scrape_x_test "$ARGUMENTS"
   ```

3. **결과 분석**: 스크래핑 결과를 테이블 형식으로 정리
   | 항목 | 값 |
   |------|-----|
   | URL | 입력 URL |
   | 트윗 ID | 추출된 ID |
   | 작성자 | screen_name |
   | 콘텐츠 길이 | 문자 수 |
   | 추출 방식 | Syndication / Playwright |
   | 소요 시간 | 초 |

4. **문제 발생 시**:
   - CSS 셀렉터 실패 → 새로운 셀렉터 제안
   - 로그인 필요 → 환경변수 확인 안내
   - 타임아웃 → 네트워크 상태 확인

## 콘텐츠 추출 우선순위

1. Syndication API (빠름, 로그인 불필요)
2. Playwright + X 아티클 본문
3. Playwright + 트윗 텍스트
4. Playwright + X Notes
5. Fallback: main 영역 텍스트

## 관련 파일

- 스크래퍼: `backend/app/services/twitter_scraper.py`
- 테스트 스크립트: `backend/samples/scrape_x_test.py`
