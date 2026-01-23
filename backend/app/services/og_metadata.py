"""
OG 메타데이터 추출 서비스

Unix Philosophy:
- Modularity: OG 메타데이터 추출만 담당
- Clarity: 명확한 단일 책임
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


@dataclass
class OGMetadata:
    """Open Graph 메타데이터"""

    title: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    fetch_failed: bool = False
    fetch_message: Optional[str] = None


def extract_og_metadata(html: str, base_url: str) -> Optional[OGMetadata]:
    """
    HTML에서 OG 메타데이터 추출

    Args:
        html: HTML 문자열
        base_url: 기본 URL (상대 경로 해석용)

    Returns:
        OGMetadata 또는 None
    """
    try:
        og_title = _extract_meta_content(html, "og:title")
        og_image = _extract_meta_content(html, "og:image")
        og_description = _extract_meta_content(html, "og:description")

        # og:title이 없으면 <title> 태그에서 추출
        if not og_title:
            title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
            if title_match:
                og_title = title_match.group(1).strip()

        # og:image 상대 경로 처리
        if og_image and not og_image.startswith(("http://", "https://")):
            og_image = urljoin(base_url, og_image)

        if og_title or og_image:
            return OGMetadata(
                title=og_title,
                image=og_image,
                description=og_description,
            )

        return None

    except Exception as e:
        logger.error(f"OG 메타데이터 추출 실패: {e}")
        return None


def _extract_meta_content(html: str, property_name: str) -> Optional[str]:
    """
    메타 태그에서 content 추출

    Args:
        html: HTML 문자열
        property_name: property 속성 값

    Returns:
        content 값 또는 None
    """
    patterns = [
        rf'<meta[^>]+property=["\']?{re.escape(property_name)}["\']?[^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']?{re.escape(property_name)}["\']?',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None
