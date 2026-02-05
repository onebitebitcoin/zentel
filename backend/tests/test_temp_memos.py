"""
임시 메모 API 테스트
"""


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
