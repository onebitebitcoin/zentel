"""
YouTube Transcript 추출 테스트
"""
from __future__ import annotations

import re
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)
import httpx


def extract_video_id(url: str) -> Optional[str]:
    """YouTube URL에서 비디오 ID 추출"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_video_metadata(video_id: str) -> dict:
    """oEmbed API로 메타데이터 추출"""
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        response = httpx.get(oembed_url, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get("title"),
                "author": data.get("author_name"),
                "thumbnail": data.get("thumbnail_url"),
            }
    except Exception as e:
        print(f"메타데이터 추출 실패: {e}")
    return {}


def get_transcript(video_id: str, languages: list = None) -> dict:
    """자막 추출 (youtube-transcript-api 1.2.x 버전)"""
    if languages is None:
        languages = ['ko', 'en', 'ja']  # 한국어, 영어, 일본어 순으로 시도

    result = {
        "success": False,
        "transcript": None,
        "language": None,
        "is_generated": False,
        "error": None,
    }

    try:
        api = YouTubeTranscriptApi()

        # 사용 가능한 자막 목록 확인
        transcript_list = api.list(video_id)

        print(f"사용 가능한 자막:")
        for transcript in transcript_list:
            print(f"  - {transcript}")

        # 자막 가져오기 (언어 우선순위 적용)
        fetched = None
        used_lang = None
        for lang in languages:
            try:
                fetched = api.fetch(video_id, languages=[lang])
                used_lang = lang
                break
            except NoTranscriptFound:
                continue

        if fetched:
            full_text = " ".join([t.text for t in fetched])
            result["success"] = True
            result["transcript"] = full_text
            result["language"] = used_lang
            result["is_generated"] = True  # 자동 생성 여부 확인 어려움
        else:
            result["error"] = "지원하는 언어의 자막을 찾을 수 없습니다."

    except TranscriptsDisabled:
        result["error"] = "이 영상은 자막이 비활성화되어 있습니다."
    except VideoUnavailable:
        result["error"] = "영상을 찾을 수 없습니다."
    except NoTranscriptFound:
        result["error"] = "사용 가능한 자막이 없습니다."
    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    # 테스트 URL
    url = "https://youtu.be/JmiZSLEy33I?si=LppqHtjepLPpRxjJ"

    print("=" * 60)
    print("YouTube Transcript 추출 테스트")
    print("=" * 60)
    print(f"URL: {url}")

    # 비디오 ID 추출
    video_id = extract_video_id(url)
    if not video_id:
        print("비디오 ID 추출 실패")
        return

    print(f"Video ID: {video_id}")
    print()

    # 메타데이터 추출
    print("1. 메타데이터 추출")
    print("-" * 40)
    metadata = get_video_metadata(video_id)
    print(f"  제목: {metadata.get('title')}")
    print(f"  채널: {metadata.get('author')}")
    print(f"  썸네일: {metadata.get('thumbnail')}")
    print()

    # 자막 추출
    print("2. 자막 추출")
    print("-" * 40)
    result = get_transcript(video_id)

    if result["success"]:
        print(f"  언어: {result['language']}")
        print(f"  길이: {len(result['transcript'])} 글자")
        print()
        print("3. 자막 내용 (처음 500자)")
        print("-" * 40)
        print(result['transcript'][:500])
        print("...")
    else:
        print(f"  실패: {result['error']}")


if __name__ == "__main__":
    main()
