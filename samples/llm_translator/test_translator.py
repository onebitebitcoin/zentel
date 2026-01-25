"""
LLM Translator 테스트

실행 방법:
    cd samples/llm_translator
    pip install -r requirements.txt
    cp .env.example .env
    # .env에 OPENAI_API_KEY 설정
    python test_translator.py
"""

import asyncio
import logging
import os
import sys

from translator import (
    TranslationResult,
    split_into_chunks,
    merge_translations,
    detect_language,
    translate_chunk,
    extract_highlights,
    translate_and_highlight,
    get_korean_ratio,
)
from config import Config, create_config

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# 테스트 데이터
# ============================================================================

SHORT_ENGLISH_TEXT = """
Artificial intelligence is transforming how we work and live.
Machine learning algorithms can now recognize patterns in data
that humans might miss. This technology is being applied across
industries, from healthcare to finance.
"""

LONG_ENGLISH_TEXT = """
The development of artificial intelligence has been one of the most
significant technological achievements of the 21st century. From its
early beginnings in the 1950s, when Alan Turing first proposed the
concept of machine intelligence, AI has evolved into a powerful tool
that touches nearly every aspect of modern life.

Today, AI systems power recommendation engines on streaming platforms,
help doctors diagnose diseases, enable autonomous vehicles to navigate
complex traffic situations, and even assist in scientific research.
The impact of these systems continues to grow as computational power
increases and algorithms become more sophisticated.

One of the most exciting developments in recent years has been the
emergence of large language models (LLMs). These systems, trained on
vast amounts of text data, can understand and generate human-like
language with remarkable accuracy. They are being used for translation,
content creation, code generation, and countless other applications.

However, the rapid advancement of AI also raises important ethical
questions. Issues of bias in training data, the potential for job
displacement, and concerns about privacy and surveillance are all
topics of ongoing debate. As we continue to develop these powerful
systems, it is crucial that we do so responsibly, with careful
consideration of their potential impacts on society.

The future of AI holds immense promise. Researchers are working on
systems that can reason, learn, and adapt in ways that more closely
mirror human cognition. While true artificial general intelligence
remains a distant goal, the incremental advances being made today
are laying the groundwork for even more transformative technologies
in the years to come.
"""

KOREAN_TEXT = """
인공지능 기술의 발전은 우리 사회에 큰 변화를 가져오고 있습니다.
머신러닝 알고리즘은 이제 인간이 놓칠 수 있는 데이터 패턴을 인식할 수 있습니다.
이 기술은 의료부터 금융까지 다양한 산업에 적용되고 있습니다.
특히 자연어 처리 분야에서의 발전은 번역, 콘텐츠 생성, 고객 서비스 등에
혁신적인 변화를 만들어내고 있습니다.
"""


# ============================================================================
# 단위 테스트 (API 호출 없음)
# ============================================================================


def test_split_into_chunks():
    """청크 분할 테스트"""
    print("\n[테스트] 청크 분할")

    # 짧은 텍스트는 분할하지 않음
    short_text = "This is a short text."
    chunks = split_into_chunks(short_text, chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0] == short_text
    print("  - 짧은 텍스트: PASS")

    # 긴 텍스트는 분할됨
    long_text = "A" * 5000
    chunks = split_into_chunks(long_text, chunk_size=2000, chunk_overlap=100)
    assert len(chunks) > 1
    print(f"  - 긴 텍스트 ({len(long_text)}자 -> {len(chunks)}개 청크): PASS")

    # 문장 경계에서 분할
    text_with_sentences = "First sentence. Second sentence. Third sentence. Fourth sentence."
    chunks = split_into_chunks(text_with_sentences, chunk_size=30, chunk_overlap=5)
    assert len(chunks) > 1
    print("  - 문장 경계 분할: PASS")

    return True


def test_merge_translations():
    """번역 합치기 테스트"""
    print("\n[테스트] 번역 합치기")

    # 단일 번역
    single = ["This is a translation."]
    result = merge_translations(single)
    assert result == single[0]
    print("  - 단일 번역: PASS")

    # 다중 번역 (겹침 없음)
    multiple = ["First part.", "Second part.", "Third part."]
    result = merge_translations(multiple)
    assert "First part" in result
    assert "Second part" in result
    assert "Third part" in result
    print("  - 다중 번역: PASS")

    # 빈 리스트
    empty = []
    result = merge_translations(empty)
    assert result == ""
    print("  - 빈 리스트: PASS")

    return True


def test_korean_ratio():
    """한국어 비율 계산 테스트"""
    print("\n[테스트] 한국어 비율 계산")

    # 순수 한국어
    korean = "안녕하세요 반갑습니다"
    ratio = get_korean_ratio(korean)
    assert ratio > 0.9
    print(f"  - 순수 한국어: {ratio:.1%} (PASS)")

    # 순수 영어
    english = "Hello world"
    ratio = get_korean_ratio(english)
    assert ratio < 0.1
    print(f"  - 순수 영어: {ratio:.1%} (PASS)")

    # 혼합
    mixed = "안녕하세요 Hello 반갑습니다 World"
    ratio = get_korean_ratio(mixed)
    assert 0.3 < ratio < 0.7
    print(f"  - 혼합 텍스트: {ratio:.1%} (PASS)")

    return True


# ============================================================================
# 통합 테스트 (API 호출 필요)
# ============================================================================


async def test_detect_language(config: Config):
    """언어 감지 테스트"""
    print("\n[테스트] 언어 감지")

    # 영어 감지
    lang = await detect_language(SHORT_ENGLISH_TEXT, config)
    assert lang == "en"
    print(f"  - 영어 텍스트: {lang} (PASS)")

    # 한국어 감지
    lang = await detect_language(KOREAN_TEXT, config)
    assert lang == "ko"
    print(f"  - 한국어 텍스트: {lang} (PASS)")

    return True


async def test_translate_chunk(config: Config):
    """청크 번역 테스트"""
    print("\n[테스트] 청크 번역")

    translation = await translate_chunk(SHORT_ENGLISH_TEXT, 0, 1, config)

    assert translation is not None
    assert len(translation) > 0
    # 한국어가 포함되어 있는지 확인
    korean_ratio = get_korean_ratio(translation)
    assert korean_ratio > 0.5

    print(f"  - 번역 결과: {len(translation)}자, 한국어 비율: {korean_ratio:.1%} (PASS)")
    print(f"  - 미리보기: {translation[:100]}...")

    return True


async def test_extract_highlights(config: Config):
    """하이라이트 추출 테스트"""
    print("\n[테스트] 하이라이트 추출")

    highlights = await extract_highlights(LONG_ENGLISH_TEXT, 3, config)

    assert isinstance(highlights, list)
    assert len(highlights) > 0
    assert len(highlights) <= 3

    print(f"  - 추출된 하이라이트: {len(highlights)}개 (PASS)")
    for i, h in enumerate(highlights):
        print(f"    [{i+1}] ({h['type']}) {h['text'][:50]}...")

    return True


async def test_translate_and_highlight_english(config: Config):
    """영어 텍스트 번역+하이라이트 테스트"""
    print("\n[테스트] 영어 텍스트 번역+하이라이트")

    result = await translate_and_highlight(SHORT_ENGLISH_TEXT, config)

    assert isinstance(result, TranslationResult)
    assert result.language == "en"
    assert result.translation is not None
    assert get_korean_ratio(result.translation) > 0.5
    assert result.chunk_count >= 1

    print(f"  - 언어: {result.language}")
    print(f"  - 번역 길이: {len(result.translation)}자")
    print(f"  - 청크 수: {result.chunk_count}")
    print(f"  - 하이라이트 수: {len(result.highlights)}")
    print("  - 결과: PASS")

    return True


async def test_translate_and_highlight_korean(config: Config):
    """한국어 텍스트 정리+하이라이트 테스트"""
    print("\n[테스트] 한국어 텍스트 정리+하이라이트")

    result = await translate_and_highlight(KOREAN_TEXT, config)

    assert isinstance(result, TranslationResult)
    assert result.language == "ko"
    # 한국어는 번역 없이 정리만 수행
    assert result.translation is not None
    assert result.chunk_count >= 1

    print(f"  - 언어: {result.language}")
    print(f"  - 정리된 텍스트 길이: {len(result.translation)}자")
    print(f"  - 청크 수: {result.chunk_count}")
    print(f"  - 하이라이트 수: {len(result.highlights)}")
    print("  - 결과: PASS")

    return True


async def test_translate_and_highlight_long(config: Config):
    """긴 텍스트 청크 분할 번역 테스트"""
    print("\n[테스트] 긴 텍스트 청크 분할 번역")

    # 청크 크기를 작게 설정하여 분할 테스트
    config.chunk_size = 500
    config.chunk_overlap = 50

    result = await translate_and_highlight(LONG_ENGLISH_TEXT, config)

    assert isinstance(result, TranslationResult)
    assert result.language == "en"
    assert result.translation is not None
    assert result.chunk_count > 1  # 여러 청크로 분할됨

    print(f"  - 원본 길이: {len(LONG_ENGLISH_TEXT)}자")
    print(f"  - 번역 길이: {len(result.translation)}자")
    print(f"  - 청크 수: {result.chunk_count}")
    print(f"  - 하이라이트 수: {len(result.highlights)}")
    print("  - 결과: PASS")

    return True


# ============================================================================
# 메인 실행
# ============================================================================


async def run_integration_tests():
    """통합 테스트 실행 (API 호출 필요)"""
    print("\n" + "=" * 60)
    print("통합 테스트 (API 호출 필요)")
    print("=" * 60)

    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n[경고] OPENAI_API_KEY가 설정되지 않았습니다.")
        print("통합 테스트를 건너뜁니다.")
        print("\n설정 방법:")
        print("  1. cp .env.example .env")
        print("  2. .env 파일에 OPENAI_API_KEY 설정")
        return False

    config = create_config()
    passed = 0
    failed = 0

    tests = [
        ("언어 감지", test_detect_language),
        ("청크 번역", test_translate_chunk),
        ("하이라이트 추출", test_extract_highlights),
        ("영어 번역+하이라이트", test_translate_and_highlight_english),
        ("한국어 정리+하이라이트", test_translate_and_highlight_korean),
        ("긴 텍스트 분할 번역", test_translate_and_highlight_long),
    ]

    for name, test_func in tests:
        try:
            await test_func(config)
            passed += 1
        except Exception as e:
            print(f"\n[실패] {name}: {e}")
            failed += 1

    return failed == 0


def run_unit_tests():
    """단위 테스트 실행 (API 호출 없음)"""
    print("\n" + "=" * 60)
    print("단위 테스트 (API 호출 없음)")
    print("=" * 60)

    passed = 0
    failed = 0

    tests = [
        ("청크 분할", test_split_into_chunks),
        ("번역 합치기", test_merge_translations),
        ("한국어 비율 계산", test_korean_ratio),
    ]

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n[실패] {name}: {e}")
            failed += 1

    return failed == 0


def main():
    """테스트 메인"""
    print("=" * 60)
    print("LLM Translator 테스트")
    print("=" * 60)

    # 단위 테스트 실행
    unit_success = run_unit_tests()

    # 통합 테스트 실행
    integration_success = asyncio.run(run_integration_tests())

    # 결과 출력
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"단위 테스트: {'PASS' if unit_success else 'FAIL'}")
    print(f"통합 테스트: {'PASS' if integration_success else 'SKIP/FAIL'}")
    print("=" * 60)

    if unit_success and integration_success:
        print("\n모든 테스트 통과!")
        sys.exit(0)
    elif unit_success:
        print("\n단위 테스트 통과 (통합 테스트는 API 키 필요)")
        sys.exit(0)
    else:
        print("\n일부 테스트 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
