"""
YouTube 스크래핑 서비스

YouTube URL에서 자막(transcript)과 메타데이터를 추출합니다:
1. oEmbed API로 메타데이터 추출 (제목, 채널명, 썸네일)
2. youtube-transcript-api로 자막 추출

- 한국어 자막 우선
- 자막 없으면 영어 자막 시도
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlparse

import httpx

from app.utils import DEFAULT_USER_AGENT

logger = logging.getLogger(__name__)


@dataclass
class YouTubeScrapingResult:
    """YouTube 스크래핑 결과"""

    content: str = ""  # 자막 전체 텍스트
    og_title: Optional[str] = None  # 영상 제목
    og_image: Optional[str] = None  # 썸네일
    og_description: Optional[str] = None  # 채널명
    success: bool = False
    error: Optional[str] = None
    language: Optional[str] = None  # 자막 언어
    video_id: Optional[str] = None  # 비디오 ID


class YouTubeScraper:
    """YouTube 스크래핑 서비스"""

    def __init__(self) -> None:
        self.user_agent = DEFAULT_USER_AGENT

    def is_youtube_url(self, url: str) -> bool:
        """
        YouTube URL인지 확인

        Args:
            url: 확인할 URL

        Returns:
            YouTube URL이면 True
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower() in [
                "youtube.com",
                "www.youtube.com",
                "m.youtube.com",
                "youtu.be",
                "www.youtu.be",
            ]
        except Exception:
            return False

    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        URL에서 비디오 ID 추출

        지원 형식:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/v/VIDEO_ID
        - https://www.youtube.com/shorts/VIDEO_ID

        Args:
            url: YouTube URL

        Returns:
            비디오 ID 또는 None
        """
        try:
            parsed = urlparse(url)

            # youtu.be 형식
            if "youtu.be" in parsed.netloc:
                # /VIDEO_ID 형식
                video_id = parsed.path.lstrip("/")
                if video_id:
                    return video_id.split("?")[0]

            # youtube.com 형식
            if "youtube.com" in parsed.netloc:
                # /watch?v=VIDEO_ID 형식
                if parsed.path == "/watch":
                    query_params = parse_qs(parsed.query)
                    video_ids = query_params.get("v")
                    if video_ids:
                        return video_ids[0]

                # /embed/VIDEO_ID, /v/VIDEO_ID, /shorts/VIDEO_ID 형식
                patterns = [
                    r"^/embed/([a-zA-Z0-9_-]+)",
                    r"^/v/([a-zA-Z0-9_-]+)",
                    r"^/shorts/([a-zA-Z0-9_-]+)",
                ]
                for pattern in patterns:
                    match = re.match(pattern, parsed.path)
                    if match:
                        return match.group(1)

            return None

        except Exception as e:
            logger.error(f"[YouTubeScraper] 비디오 ID 추출 실패: {e}")
            return None

    async def _get_metadata(self, video_id: str) -> dict:
        """
        oEmbed API로 메타데이터 추출

        Args:
            video_id: YouTube 비디오 ID

        Returns:
            메타데이터 딕셔너리 (title, author_name, thumbnail_url)
        """
        metadata = {}

        try:
            oembed_url = (
                f"https://www.youtube.com/oembed?"
                f"url=https://www.youtube.com/watch?v={video_id}&format=json"
            )

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    oembed_url,
                    headers={"User-Agent": self.user_agent},
                )

                if response.status_code == 200:
                    data = response.json()
                    metadata["title"] = data.get("title")
                    metadata["author_name"] = data.get("author_name")
                    metadata["thumbnail_url"] = data.get("thumbnail_url")

                    # 고해상도 썸네일 URL 생성
                    if video_id:
                        metadata["thumbnail_url"] = (
                            f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                        )

                    logger.info(
                        f"[YouTubeScraper] oEmbed 메타데이터 추출 성공: "
                        f"title={metadata.get('title')}"
                    )
                else:
                    logger.warning(
                        f"[YouTubeScraper] oEmbed API 실패: status={response.status_code}"
                    )

        except Exception as e:
            logger.error(f"[YouTubeScraper] 메타데이터 추출 실패: {e}")

        return metadata

    async def _get_transcript(self, video_id: str) -> tuple[Optional[str], Optional[str]]:
        """
        youtube-transcript-api로 자막 추출

        Args:
            video_id: YouTube 비디오 ID

        Returns:
            (자막 텍스트, 언어 코드) 튜플
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._errors import (
                NoTranscriptFound,
                TranscriptsDisabled,
                VideoUnavailable,
            )

            # 한국어 자막 우선 시도
            preferred_languages = ["ko", "en", "en-US", "en-GB"]

            # YouTubeTranscriptApi 인스턴스 생성 (v1.x API)
            ytt_api = YouTubeTranscriptApi()

            try:
                # 먼저 fetch로 직접 시도 (간단한 경우)
                try:
                    transcript_data = ytt_api.fetch(video_id, languages=preferred_languages)
                    language = "auto"

                    # 텍스트만 추출하여 합치기
                    texts = [entry.text for entry in transcript_data]
                    full_text = " ".join(texts)

                    # 너무 긴 자막은 자르기 (약 10000자)
                    if len(full_text) > 10000:
                        full_text = full_text[:10000] + "..."

                    logger.info(
                        f"[YouTubeScraper] 자막 추출 성공 (fetch): "
                        f"length={len(full_text)}"
                    )
                    return full_text, language

                except NoTranscriptFound:
                    # 선호 언어 자막이 없으면 목록에서 찾기
                    pass

                # 자막 목록 조회
                transcript_list = ytt_api.list(video_id)
                transcript = None
                language = None

                # 수동 자막 먼저 시도
                for lang in preferred_languages:
                    try:
                        transcript = transcript_list.find_transcript([lang])
                        language = lang
                        logger.info(f"[YouTubeScraper] 수동 자막 발견: {lang}")
                        break
                    except NoTranscriptFound:
                        continue

                # 수동 자막 없으면 자동 생성 자막 시도
                if transcript is None:
                    try:
                        transcript = transcript_list.find_generated_transcript(
                            preferred_languages
                        )
                        language = "auto"
                        logger.info("[YouTubeScraper] 자동 생성 자막 사용")
                    except NoTranscriptFound:
                        # 아무 자막이나 가져오기
                        try:
                            available = list(transcript_list)
                            if available:
                                transcript = available[0]
                                language = transcript.language_code
                                logger.info(
                                    f"[YouTubeScraper] 사용 가능한 자막 사용: {language}"
                                )
                        except Exception:
                            pass

                if transcript:
                    # 자막 데이터 가져오기
                    transcript_data = transcript.fetch()

                    # 텍스트만 추출하여 합치기
                    texts = [entry.text for entry in transcript_data]
                    full_text = " ".join(texts)

                    # 너무 긴 자막은 자르기 (약 10000자)
                    if len(full_text) > 10000:
                        full_text = full_text[:10000] + "..."

                    logger.info(
                        f"[YouTubeScraper] 자막 추출 성공 (list): "
                        f"language={language}, length={len(full_text)}"
                    )
                    return full_text, language

            except TranscriptsDisabled:
                logger.warning("[YouTubeScraper] 자막이 비활성화된 영상입니다")
                return None, None

            except VideoUnavailable:
                logger.warning("[YouTubeScraper] 영상을 찾을 수 없습니다")
                return None, None

            except NoTranscriptFound:
                logger.warning("[YouTubeScraper] 사용 가능한 자막이 없습니다")
                return None, None

        except ImportError:
            logger.error(
                "[YouTubeScraper] youtube-transcript-api 패키지가 설치되지 않았습니다"
            )
            return None, None

        except Exception as e:
            logger.error(f"[YouTubeScraper] 자막 추출 실패: {e}", exc_info=True)
            return None, None

        return None, None

    async def scrape(self, url: str) -> YouTubeScrapingResult:
        """
        YouTube URL의 컨텐츠를 추출

        Args:
            url: 스크래핑할 URL

        Returns:
            YouTubeScrapingResult
        """
        result = YouTubeScrapingResult()

        # 비디오 ID 추출
        video_id = self._extract_video_id(url)
        if not video_id:
            logger.warning(f"[YouTubeScraper] 비디오 ID 추출 실패: {url}")
            result.error = "비디오 ID를 추출할 수 없습니다"
            return result

        result.video_id = video_id
        logger.info(f"[YouTubeScraper] 스크래핑 시작: video_id={video_id}")

        # 메타데이터 추출
        metadata = await self._get_metadata(video_id)
        result.og_title = metadata.get("title")
        result.og_description = metadata.get("author_name")  # 채널명
        result.og_image = metadata.get("thumbnail_url")

        # 자막 추출
        transcript, language = await self._get_transcript(video_id)
        if transcript:
            result.content = transcript
            result.language = language
            result.success = True
            logger.info(
                f"[YouTubeScraper] 스크래핑 완료: "
                f"title={result.og_title}, content_length={len(result.content)}"
            )
        else:
            # 자막이 없어도 메타데이터가 있으면 부분 성공
            if result.og_title:
                result.success = True
                result.content = f"[자막 없음] {result.og_title}"
                logger.info(
                    f"[YouTubeScraper] 자막 없음, 메타데이터만 추출: title={result.og_title}"
                )
            else:
                result.error = "자막과 메타데이터 추출 실패"
                logger.warning(f"[YouTubeScraper] 스크래핑 실패: {result.error}")

        return result


# 싱글톤 인스턴스
youtube_scraper = YouTubeScraper()
