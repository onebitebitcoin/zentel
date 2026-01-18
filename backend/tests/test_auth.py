"""
인증 API 테스트
"""


class TestRegister:
    """회원가입 테스트"""

    def test_register_success(self, client):
        """회원가입 성공"""
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert "id" in data
        assert data["is_active"] is True

    def test_register_duplicate_username(self, client):
        """중복된 사용자 이름으로 가입 실패"""
        # 첫 번째 가입
        client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )

        # 동일한 사용자 이름으로 두 번째 가입 시도
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password456"},
        )
        assert response.status_code == 409
        assert "이미 사용 중인 사용자 이름" in response.json()["detail"]

    def test_register_short_username(self, client):
        """짧은 사용자 이름으로 가입 실패"""
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "ab", "password": "password123"},
        )
        assert response.status_code == 422

    def test_register_short_password(self, client):
        """짧은 비밀번호로 가입 실패"""
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "pass"},
        )
        assert response.status_code == 422

    def test_register_invalid_username(self, client):
        """잘못된 형식의 사용자 이름으로 가입 실패"""
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "test@user", "password": "password123"},
        )
        assert response.status_code == 422


class TestLogin:
    """로그인 테스트"""

    def test_login_success(self, client):
        """로그인 성공"""
        # 사용자 등록
        client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )

        # 로그인
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_wrong_password(self, client):
        """잘못된 비밀번호로 로그인 실패"""
        # 사용자 등록
        client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )

        # 잘못된 비밀번호로 로그인
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """존재하지 않는 사용자로 로그인 실패"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password123"},
        )
        assert response.status_code == 401


class TestCurrentUser:
    """현재 사용자 정보 조회 테스트"""

    def test_get_current_user_success(self, client):
        """현재 사용자 정보 조회 성공"""
        # 사용자 등록 및 로그인
        client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"},
        )
        access_token = login_response.json()["access_token"]

        # 현재 사용자 정보 조회
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    def test_get_current_user_no_token(self, client):
        """토큰 없이 현재 사용자 정보 조회 실패"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """잘못된 토큰으로 현재 사용자 정보 조회 실패"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401


class TestRefreshToken:
    """토큰 갱신 테스트"""

    def test_refresh_token_success(self, client):
        """토큰 갱신 성공 - 쿠키로 refresh_token 전송"""
        # 사용자 등록 및 로그인
        client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"},
        )

        # 로그인 응답의 쿠키가 자동으로 클라이언트에 설정됨
        # 토큰 갱신 (쿠키 자동 전송)
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_refresh_token_no_cookie(self, client):
        """쿠키 없이 토큰 갱신 실패"""
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 401

    def test_refresh_token_invalid_cookie(self, client):
        """잘못된 refresh_token 쿠키로 갱신 실패"""
        client.cookies.set("refresh_token", "invalid_refresh_token")
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 401


class TestCheckUsername:
    """사용자 이름 중복 체크 테스트"""

    def test_check_username_available(self, client):
        """사용 가능한 사용자 이름"""
        response = client.get("/api/v1/auth/check-username?username=newuser")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True

    def test_check_username_taken(self, client):
        """이미 사용 중인 사용자 이름"""
        # 사용자 등록
        client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )

        # 중복 체크
        response = client.get("/api/v1/auth/check-username?username=testuser")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False

    def test_check_username_too_short(self, client):
        """너무 짧은 사용자 이름"""
        response = client.get("/api/v1/auth/check-username?username=ab")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False


class TestLogout:
    """로그아웃 테스트"""

    def test_logout_success(self, client):
        """로그아웃 성공"""
        # 사용자 등록 및 로그인
        client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password123"},
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"},
        )
        access_token = login_response.json()["access_token"]

        # 로그아웃
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert "로그아웃" in response.json()["message"]

    def test_logout_no_token(self, client):
        """토큰 없이 로그아웃 실패"""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401
