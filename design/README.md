# Design Reference Guide

이 폴더에 디자인 레퍼런스 이미지를 넣어주세요.
Claude Code가 이미지를 분석하여 UI 스타일을 적용합니다.

## 폴더 구조

```
design/
├── reference/           # 레퍼런스 이미지를 여기에 넣으세요
│   ├── dashboard.png    # 대시보드 레이아웃
│   ├── mobile.png       # 모바일 화면
│   ├── components.png   # 컴포넌트 스타일
│   └── colors.png       # 색상 팔레트
└── README.md            # 이 파일
```

## 레퍼런스 이미지 가이드

### 권장 이미지 종류

1. **대시보드 레이아웃** - 전체 화면 구성, 카드 배치
2. **모바일 화면** - 모바일 반응형 디자인
3. **컴포넌트** - 버튼, 입력창, 테이블 등 UI 컴포넌트
4. **색상 팔레트** - 메인 색상, 포인트 색상

### 좋은 레퍼런스 예시

- Dribbble, Behance에서 찾은 UI 디자인
- 참고하고 싶은 웹사이트 스크린샷
- Figma/Sketch 디자인 Export
- 직접 그린 와이어프레임

### 지원 파일 형식

- PNG (권장)
- JPG / JPEG
- WebP

## 사용 방법

1. 이 폴더(`design/reference/`)에 이미지 파일 추가
2. Claude Code에게 "프로젝트 생성해줘" 또는 "UI 만들어줘" 요청
3. Claude Code가 자동으로 이미지를 분석하여 스타일 적용

## 이미지가 없는 경우

이미지가 없으면 Claude Code가 다음과 같이 질문합니다:

```
"design/reference 폴더에 레퍼런스 이미지가 없습니다.
어떤 스타일로 디자인할까요?
1. 깔끔한 미니멀 스타일
2. 금융 앱 스타일 (네이버페이, 토스)
3. 기본 TailwindCSS 스타일
4. 직접 설명해주세요"
```

## 예시

Dribbble에서 "finance dashboard"로 검색하면 좋은 레퍼런스를 찾을 수 있습니다:
- https://dribbble.com/search/finance-dashboard
- https://dribbble.com/search/stock-portfolio
