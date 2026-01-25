# LLM Translator

텍스트 번역 및 하이라이트 추출 모듈입니다. 다른 AI 코딩 프로젝트에서 재사용할 수 있도록 독립적으로 설계되었습니다.

## 핵심 기능

- **자동 언어 감지**: 텍스트의 언어를 자동으로 감지 (ISO 639-1 코드)
- **한국어 번역**: 비한국어 텍스트를 자연스러운 한국어로 번역
- **청크 분할**: 긴 텍스트를 문장 단위로 분할하여 처리
- **하이라이트 추출**: 핵심 주장(claim)과 흥미로운 사실(fact) 추출
- **텍스트 정리**: 불필요한 특수문자 제거 및 문단 구조화

## 설치

```bash
cd samples/llm_translator
pip install -r requirements.txt
```

## 환경 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 OpenAI API 키를 설정합니다:

```
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

## 사용 예시

### 기본 사용법

```python
import asyncio
from translator import translate_and_highlight

async def main():
    text = """
    Artificial intelligence is transforming how we work and live.
    Machine learning algorithms can now recognize patterns in data
    that humans might miss.
    """

    result = await translate_and_highlight(text)

    print(f"원본 언어: {result.language}")
    print(f"번역: {result.translation}")
    print(f"청크 수: {result.chunk_count}")
    print(f"하이라이트: {result.highlights}")

asyncio.run(main())
```

### 커스텀 설정 사용

```python
from translator import translate_and_highlight
from config import create_config

config = create_config(
    api_key="your-api-key",
    model="gpt-4o",
    chunk_size=2000,
    max_highlights=3,
)

result = await translate_and_highlight(text, config)
```

### 개별 함수 사용

```python
from translator import (
    detect_language,
    split_into_chunks,
    translate_chunk,
    merge_translations,
    extract_highlights,
)

# 언어 감지
language = await detect_language(text)

# 청크 분할
chunks = split_into_chunks(text, chunk_size=3000, chunk_overlap=200)

# 각 청크 번역
translations = []
for i, chunk in enumerate(chunks):
    translated = await translate_chunk(chunk, i, len(chunks))
    translations.append(translated)

# 번역 합치기
full_translation = merge_translations(translations)

# 하이라이트 추출
highlights = await extract_highlights(full_translation, max_count=5)
```

## API 참조

### TranslationResult

번역 결과 데이터 클래스입니다.

```python
@dataclass
class TranslationResult:
    language: str           # 원본 언어 코드 (ISO 639-1)
    translation: str        # 번역/정리된 텍스트
    highlights: list[dict]  # 하이라이트 목록
    chunk_count: int        # 처리된 청크 수
```

### 함수

| 함수 | 설명 | 반환 타입 |
|------|------|----------|
| `translate_and_highlight(text, config)` | 메인 함수: 언어 감지 + 번역 + 하이라이트 | `TranslationResult` |
| `detect_language(text, config)` | 언어 감지 | `str` |
| `translate_chunk(chunk, index, total, config)` | 단일 청크 번역 | `str` |
| `extract_highlights(text, max_count, config)` | 하이라이트 추출 | `list[dict]` |
| `split_into_chunks(text, chunk_size, overlap)` | 텍스트 청크 분할 | `list[str]` |
| `merge_translations(translations)` | 번역 결과 합치기 | `str` |

### Config

설정 클래스입니다.

| 속성 | 기본값 | 설명 |
|------|--------|------|
| `api_key` | 환경변수 | OpenAI API 키 |
| `model` | `gpt-4o-mini` | 사용할 모델 |
| `chunk_size` | `3000` | 청크 크기 (문자) |
| `chunk_overlap` | `200` | 청크 간 겹침 (문자) |
| `max_highlights` | `5` | 최대 하이라이트 수 |

## 테스트 실행

```bash
python test_translator.py
```

단위 테스트는 API 호출 없이 실행됩니다. 통합 테스트는 `OPENAI_API_KEY` 설정이 필요합니다.

## 확장 가이드

### 다른 LLM 제공자 지원

`translator.py`의 `get_client()` 함수를 수정하여 다른 LLM API를 사용할 수 있습니다:

```python
def get_client(config: Config):
    if config.provider == "anthropic":
        from anthropic import Anthropic
        return Anthropic(api_key=config.api_key)
    # 기본: OpenAI
    return OpenAI(api_key=config.api_key)
```

### 다른 타겟 언어 지원

번역 프롬프트를 수정하여 다른 언어로 번역할 수 있습니다:

```python
async def translate_chunk(chunk, target_language="ko", ...):
    instructions = f"주어진 텍스트를 {target_language}로 번역하세요..."
```

### 하이라이트 타입 추가

`extract_highlights()` 함수의 프롬프트를 수정하여 추가 타입을 지원할 수 있습니다:

```python
instructions = """
유형:
- claim: 핵심 주장
- fact: 흥미로운 사실
- quote: 인용문
- statistic: 통계 데이터
"""
```

## 라이선스

MIT License
