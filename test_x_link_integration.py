"""
X 링크 분석 통합 테스트
개발 서버에서 실제 분석 프로세스를 테스트합니다.
"""
import asyncio
import sys
import time
from datetime import datetime

# Backend 경로 추가
sys.path.insert(0, 'backend')

from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.temp_memo import TempMemo
from app.services.analysis_service import analysis_service
from app.core.security import get_password_hash


async def test_x_link_analysis():
    """X 링크 분석 테스트"""
    print("\n" + "="*80)
    print("X 링크 분석 통합 테스트")
    print("="*80 + "\n")

    # 테이블 생성
    Base.metadata.create_all(bind=engine)

    # DB 세션 생성
    db = SessionLocal()

    try:
        # 1. 테스트 사용자 생성
        print("1️⃣ 테스트 사용자 생성 중...")
        test_username = f"testuser_{int(time.time())}"
        user = User(
            username=test_username,
            hashed_password=get_password_hash("testpass123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"   ✅ 사용자 생성: {user.username} (ID: {user.id})")

        # 2. X 링크 메모 생성
        print("\n2️⃣ X 링크 메모 생성 중...")
        x_url = "https://x.com/i/status/2016556592561574118"
        memo = TempMemo(
            user_id=user.id,
            memo_type="EXTERNAL_SOURCE",
            content="X 아티클 테스트",
            source_url=x_url,
            analysis_status="pending",
        )
        db.add(memo)
        db.commit()
        db.refresh(memo)
        print(f"   ✅ 메모 생성: ID={memo.id}")
        print(f"   📎 URL: {x_url}")

        # 3. 분석 실행
        print("\n3️⃣ AI 분석 시작...")
        print(f"   ⏱️  시작 시간: {datetime.now().strftime('%H:%M:%S')}")
        print(f"   ⚠️  이 작업은 최대 90초 소요될 수 있습니다.\n")

        start_time = time.time()

        # 분석 실행
        await analysis_service.run_analysis(memo.id, db, user.id)

        elapsed = time.time() - start_time

        # 4. 결과 확인
        db.refresh(memo)
        print(f"\n4️⃣ 분석 결과")
        print(f"   ⏱️  소요 시간: {elapsed:.2f}초")
        print(f"   📊 상태: {memo.analysis_status}")

        if memo.analysis_status == "completed":
            print(f"   ✅ 분석 성공!")
            print(f"   📝 Context: {memo.context[:100] if memo.context else 'None'}...")
            print(f"   📄 Summary: {memo.summary[:100] if memo.summary else 'None'}...")
            print(f"   🏷️  Interests: {memo.interests}")
            print(f"   📰 OG Title: {memo.og_title}")
            print(f"   🖼️  OG Image: {memo.og_image[:50] if memo.og_image else 'None'}...")
            print(f"   📊 Fetched Content: {len(memo.fetched_content) if memo.fetched_content else 0}자")
        elif memo.analysis_status == "failed":
            print(f"   ❌ 분석 실패!")
            print(f"   🔍 에러: {memo.analysis_error}")
        else:
            print(f"   ⚠️  예상치 못한 상태: {memo.analysis_status}")

        # 5. 메모 정리
        print("\n5️⃣ 테스트 데이터 정리 중...")
        db.delete(memo)
        db.delete(user)
        db.commit()
        print("   ✅ 정리 완료")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    print("\n" + "="*80)
    print("테스트 완료")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_x_link_analysis())
