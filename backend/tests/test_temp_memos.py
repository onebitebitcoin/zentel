"""
임시 메모 API 테스트
"""

from app.models.temp_memo import TempMemo


def test_create_temp_memo(authenticated_client):
    """임시 메모 생성 테스트"""
    response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "테스트 아이디어"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["memo_type"] == "NEW_IDEA"
    assert data["content"] == "테스트 아이디어"
    assert "id" in data
    assert data["id"].startswith("tm_")
    assert "created_at" in data


def test_create_temp_memo_all_types(authenticated_client):
    """모든 메모 타입 생성 테스트"""
    memo_types = [
        "NEW_IDEA",
        "NEW_GOAL",
        "EVOLVED_THOUGHT",
        "CURIOSITY",
        "UNRESOLVED_PROBLEM",
        "EMOTION",
    ]

    for memo_type in memo_types:
        response = authenticated_client.post(
            "/api/v1/temp-memos",
            json={"memo_type": memo_type, "content": f"테스트 {memo_type}"},
        )
        assert response.status_code == 201
        assert response.json()["memo_type"] == memo_type


def test_create_temp_memo_invalid_type(authenticated_client):
    """잘못된 메모 타입 테스트"""
    response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "INVALID_TYPE", "content": "테스트"},
    )

    assert response.status_code == 422


def test_create_temp_memo_empty_content(authenticated_client):
    """빈 내용 테스트"""
    response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": ""},
    )

    assert response.status_code == 422


def test_create_temp_memo_without_auth(client):
    """인증 없이 메모 생성 시 401 반환"""
    response = client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "테스트"},
    )

    assert response.status_code == 401


def test_list_temp_memos(authenticated_client):
    """임시 메모 목록 조회 테스트"""
    # 메모 3개 생성
    for i in range(3):
        authenticated_client.post(
            "/api/v1/temp-memos",
            json={"memo_type": "NEW_IDEA", "content": f"메모 {i}"},
        )

    response = authenticated_client.get("/api/v1/temp-memos")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_list_temp_memos_without_auth(client):
    """인증 없이 목록 조회 시 401 반환"""
    response = client.get("/api/v1/temp-memos")

    assert response.status_code == 401


def test_list_temp_memos_latest_first(authenticated_client):
    """최신순 정렬 테스트"""
    # 메모 생성
    authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "첫 번째 메모"},
    )
    authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_GOAL", "content": "두 번째 메모"},
    )

    response = authenticated_client.get("/api/v1/temp-memos")
    data = response.json()

    # 최신 메모가 먼저
    assert data["items"][0]["content"] == "두 번째 메모"
    assert data["items"][1]["content"] == "첫 번째 메모"


def test_list_temp_memos_filter_by_type(authenticated_client):
    """타입별 필터링 테스트"""
    authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "아이디어"},
    )
    authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "EMOTION", "content": "감정"},
    )

    response = authenticated_client.get("/api/v1/temp-memos?type=NEW_IDEA")
    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["memo_type"] == "NEW_IDEA"


def test_list_temp_memos_pagination(authenticated_client):
    """페이지네이션 테스트"""
    for i in range(5):
        authenticated_client.post(
            "/api/v1/temp-memos",
            json={"memo_type": "NEW_IDEA", "content": f"메모 {i}"},
        )

    response = authenticated_client.get("/api/v1/temp-memos?limit=2&offset=0")
    data = response.json()

    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["next_offset"] == 2

    response = authenticated_client.get("/api/v1/temp-memos?limit=2&offset=4")
    data = response.json()

    assert len(data["items"]) == 1
    assert data["next_offset"] is None


def test_get_temp_memo(authenticated_client):
    """임시 메모 상세 조회 테스트"""
    create_response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "CURIOSITY", "content": "궁금한 것"},
    )
    memo_id = create_response.json()["id"]

    response = authenticated_client.get(f"/api/v1/temp-memos/{memo_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == memo_id
    assert data["memo_type"] == "CURIOSITY"
    assert data["content"] == "궁금한 것"


def test_get_temp_memo_not_found(authenticated_client):
    """존재하지 않는 메모 조회 테스트"""
    response = authenticated_client.get("/api/v1/temp-memos/nonexistent")

    assert response.status_code == 404


def test_get_temp_memo_without_auth(client):
    """인증 없이 상세 조회 시 401 반환"""
    response = client.get("/api/v1/temp-memos/someid")

    assert response.status_code == 401


def test_update_temp_memo(authenticated_client):
    """임시 메모 수정 테스트"""
    create_response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "원래 내용"},
    )
    memo_id = create_response.json()["id"]

    response = authenticated_client.patch(
        f"/api/v1/temp-memos/{memo_id}",
        json={"content": "수정된 내용"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "수정된 내용"
    assert data["updated_at"] is not None


def test_update_temp_memo_type(authenticated_client):
    """임시 메모 타입 수정 테스트"""
    create_response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "내용"},
    )
    memo_id = create_response.json()["id"]

    response = authenticated_client.patch(
        f"/api/v1/temp-memos/{memo_id}",
        json={"memo_type": "NEW_GOAL"},
    )

    assert response.status_code == 200
    assert response.json()["memo_type"] == "NEW_GOAL"


def test_update_temp_memo_not_found(authenticated_client):
    """존재하지 않는 메모 수정 테스트"""
    response = authenticated_client.patch(
        "/api/v1/temp-memos/nonexistent",
        json={"content": "수정 시도"},
    )

    assert response.status_code == 404


def test_delete_temp_memo(authenticated_client):
    """임시 메모 삭제 테스트"""
    create_response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "EMOTION", "content": "삭제할 메모"},
    )
    memo_id = create_response.json()["id"]

    response = authenticated_client.delete(f"/api/v1/temp-memos/{memo_id}")

    assert response.status_code == 204

    # 삭제 확인
    get_response = authenticated_client.get(f"/api/v1/temp-memos/{memo_id}")
    assert get_response.status_code == 404


def test_delete_temp_memo_not_found(authenticated_client):
    """존재하지 않는 메모 삭제 테스트"""
    response = authenticated_client.delete("/api/v1/temp-memos/nonexistent")

    assert response.status_code == 404


def test_delete_temp_memo_without_auth(client):
    """인증 없이 삭제 시 401 반환"""
    response = client.delete("/api/v1/temp-memos/someid")

    assert response.status_code == 401


def test_memo_user_isolation(authenticated_client, client):
    """사용자별 메모 분리 테스트 - 다른 사용자의 메모는 볼 수 없음"""
    # 첫 번째 사용자가 메모 생성
    create_response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "첫 번째 사용자 메모"},
    )
    memo_id = create_response.json()["id"]

    # 두 번째 사용자 생성 및 로그인
    client.post(
        "/api/v1/auth/register",
        json={"username": "seconduser", "password": "testpass123"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "seconduser", "password": "testpass123"},
    )
    access_token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {access_token}"

    # 두 번째 사용자가 첫 번째 사용자의 메모를 조회 시도 -> 404
    response = client.get(f"/api/v1/temp-memos/{memo_id}")
    assert response.status_code == 404

    # 두 번째 사용자의 메모 목록은 비어있음
    list_response = client.get("/api/v1/temp-memos")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 0


def test_health_check(client):
    """헬스 체크 테스트"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root(client):
    """루트 엔드포인트 테스트"""
    response = client.get("/")

    assert response.status_code == 200
    assert "MyRottenApple API" in response.json()["message"]


# === 검색 기능 테스트 ===


def test_search_by_context(authenticated_client, db_session):
    """context 필드 검색 테스트"""
    # 메모 생성
    response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "테스트 내용"},
    )
    memo_id = response.json()["id"]

    # DB에서 직접 context 업데이트
    memo = db_session.query(TempMemo).filter(TempMemo.id == memo_id).first()
    memo.context = "인공지능 기술에 대한 생각"
    db_session.commit()

    # context에서 검색
    search_response = authenticated_client.get("/api/v1/temp-memos?search=인공지능")
    data = search_response.json()

    assert search_response.status_code == 200
    assert data["total"] == 1
    assert data["items"][0]["id"] == memo_id


def test_search_by_summary(authenticated_client, db_session):
    """summary 필드 검색 테스트"""
    # 메모 생성
    response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "CURIOSITY", "content": "테스트 내용"},
    )
    memo_id = response.json()["id"]

    # DB에서 직접 summary 업데이트
    memo = db_session.query(TempMemo).filter(TempMemo.id == memo_id).first()
    memo.summary = "머신러닝 모델 학습 방법"
    db_session.commit()

    # summary에서 검색
    search_response = authenticated_client.get("/api/v1/temp-memos?search=머신러닝")
    data = search_response.json()

    assert search_response.status_code == 200
    assert data["total"] == 1
    assert data["items"][0]["id"] == memo_id


def test_search_not_in_content(authenticated_client, db_session):
    """content 필드는 검색 대상이 아님"""
    # 메모 생성 (content에만 키워드 존재)
    response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "블록체인 기술 연구"},
    )
    memo_id = response.json()["id"]

    # context, summary는 비어있음 (또는 다른 내용)
    memo = db_session.query(TempMemo).filter(TempMemo.id == memo_id).first()
    memo.context = "일반적인 맥락"
    memo.summary = "일반적인 요약"
    db_session.commit()

    # content에만 있는 키워드로 검색 -> 결과 없음
    search_response = authenticated_client.get("/api/v1/temp-memos?search=블록체인")
    data = search_response.json()

    assert search_response.status_code == 200
    assert data["total"] == 0


def test_search_case_insensitive(authenticated_client, db_session):
    """대소문자 무시 검색 테스트"""
    # 메모 생성
    response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "테스트"},
    )
    memo_id = response.json()["id"]

    # DB에서 직접 context 업데이트 (대문자 포함)
    memo = db_session.query(TempMemo).filter(TempMemo.id == memo_id).first()
    memo.context = "PYTHON Programming Guide"
    db_session.commit()

    # 소문자로 검색
    search_response = authenticated_client.get("/api/v1/temp-memos?search=python")
    data = search_response.json()

    assert search_response.status_code == 200
    assert data["total"] == 1

    # 대문자로 검색
    search_response2 = authenticated_client.get("/api/v1/temp-memos?search=PROGRAMMING")
    data2 = search_response2.json()

    assert data2["total"] == 1


def test_search_with_type_filter(authenticated_client, db_session):
    """타입 필터 + 검색 동시 사용 테스트"""
    # NEW_IDEA 타입 메모 생성
    response1 = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "테스트1"},
    )
    memo1_id = response1.json()["id"]

    # CURIOSITY 타입 메모 생성
    response2 = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "CURIOSITY", "content": "테스트2"},
    )
    memo2_id = response2.json()["id"]

    # 두 메모 모두 같은 키워드로 context 설정
    memo1 = db_session.query(TempMemo).filter(TempMemo.id == memo1_id).first()
    memo1.context = "딥러닝 관련 아이디어"
    memo2 = db_session.query(TempMemo).filter(TempMemo.id == memo2_id).first()
    memo2.context = "딥러닝 궁금한 점"
    db_session.commit()

    # 키워드만 검색 -> 2개
    search_all = authenticated_client.get("/api/v1/temp-memos?search=딥러닝")
    assert search_all.json()["total"] == 2

    # 타입 필터 + 검색 -> 1개
    search_filtered = authenticated_client.get(
        "/api/v1/temp-memos?type=NEW_IDEA&search=딥러닝"
    )
    data = search_filtered.json()

    assert data["total"] == 1
    assert data["items"][0]["memo_type"] == "NEW_IDEA"


def test_search_no_results(authenticated_client, db_session):
    """검색 결과 없음 테스트"""
    # 메모 생성
    response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "테스트"},
    )
    memo_id = response.json()["id"]

    memo = db_session.query(TempMemo).filter(TempMemo.id == memo_id).first()
    memo.context = "일반적인 내용"
    memo.summary = "요약 내용"
    db_session.commit()

    # 존재하지 않는 키워드로 검색
    search_response = authenticated_client.get("/api/v1/temp-memos?search=존재하지않는키워드xyz")
    data = search_response.json()

    assert search_response.status_code == 200
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_search_partial_match(authenticated_client, db_session):
    """부분 일치 검색 테스트"""
    # 메모 생성
    response = authenticated_client.post(
        "/api/v1/temp-memos",
        json={"memo_type": "NEW_IDEA", "content": "테스트"},
    )
    memo_id = response.json()["id"]

    memo = db_session.query(TempMemo).filter(TempMemo.id == memo_id).first()
    memo.context = "자연어처리 기술 연구"
    db_session.commit()

    # 부분 문자열로 검색
    search_response = authenticated_client.get("/api/v1/temp-memos?search=자연어")
    assert search_response.json()["total"] == 1

    search_response2 = authenticated_client.get("/api/v1/temp-memos?search=처리")
    assert search_response2.json()["total"] == 1
