"""
CliqUp Backend API Tests
========================
Comprehensive tests for all API endpoints including:
- Authentication (signup, login, me)
- Profiles (get, update, follow/unfollow)
- Meet/Dating (status, age-assure, squads, discover, swipe, matches)
- Social (posts, feed, reactions)
- Messaging (conversations, messages)
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data prefix for cleanup
TEST_PREFIX = "TEST_"


class TestHealthCheck:
    """Health check endpoint tests - run first"""
    
    def test_health_endpoint(self):
        """Test health check returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app"] == "CliqUp"
        assert "version" in data


class TestAuthentication:
    """Authentication endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup unique test data for each test"""
        self.unique_id = str(uuid.uuid4())[:8]
        self.test_email = f"{TEST_PREFIX}user_{self.unique_id}@cliqup.com"
        self.test_handle = f"{TEST_PREFIX}user{self.unique_id}"
        self.test_password = "testpass123"
        # Adult DOB (25 years old)
        self.adult_dob = (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d")
        # Teen DOB (16 years old)
        self.teen_dob = (datetime.now() - timedelta(days=365*16)).strftime("%Y-%m-%d")
    
    def test_signup_success_adult(self):
        """Test successful signup for adult user"""
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "dob": self.adult_dob,
            "display_name": f"Test User {self.unique_id}",
            "handle": self.test_handle
        }
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        assert response.status_code == 201, f"Signup failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == self.test_email
        assert data["user"]["handle"] == self.test_handle.lower()
        assert data["user"]["age_band"] == "adult"
    
    def test_signup_success_teen(self):
        """Test successful signup for teen user"""
        teen_email = f"{TEST_PREFIX}teen_{self.unique_id}@cliqup.com"
        teen_handle = f"{TEST_PREFIX}teen{self.unique_id}"
        
        payload = {
            "email": teen_email,
            "password": self.test_password,
            "dob": self.teen_dob,
            "display_name": f"Teen User {self.unique_id}",
            "handle": teen_handle
        }
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        assert response.status_code == 201, f"Signup failed: {response.text}"
        
        data = response.json()
        assert data["user"]["age_band"] == "teen"
    
    def test_signup_duplicate_email(self):
        """Test signup with duplicate email fails"""
        # First signup
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "dob": self.adult_dob,
            "display_name": f"Test User {self.unique_id}",
            "handle": self.test_handle
        }
        response1 = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        assert response1.status_code == 201
        
        # Second signup with same email
        payload["handle"] = f"{TEST_PREFIX}other{self.unique_id}"
        response2 = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        assert response2.status_code == 400
        assert "already in use" in response2.json().get("detail", "").lower()
    
    def test_signup_duplicate_handle(self):
        """Test signup with duplicate handle fails"""
        # First signup
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "dob": self.adult_dob,
            "display_name": f"Test User {self.unique_id}",
            "handle": self.test_handle
        }
        response1 = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        assert response1.status_code == 201
        
        # Second signup with same handle
        payload["email"] = f"{TEST_PREFIX}other_{self.unique_id}@cliqup.com"
        response2 = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        assert response2.status_code == 400
        assert "handle" in response2.json().get("detail", "").lower()
    
    def test_signup_invalid_password(self):
        """Test signup with short password fails"""
        payload = {
            "email": self.test_email,
            "password": "short",  # Less than 8 chars
            "dob": self.adult_dob,
            "display_name": f"Test User {self.unique_id}",
            "handle": self.test_handle
        }
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_login_success(self):
        """Test successful login"""
        # First signup
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "dob": self.adult_dob,
            "display_name": f"Test User {self.unique_id}",
            "handle": self.test_handle
        }
        requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        
        # Then login
        login_payload = {
            "email": self.test_email,
            "password": self.test_password
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == self.test_email
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password fails"""
        # First signup
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "dob": self.adult_dob,
            "display_name": f"Test User {self.unique_id}",
            "handle": self.test_handle
        }
        requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        
        # Login with wrong password
        login_payload = {
            "email": self.test_email,
            "password": "wrongpassword"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        assert response.status_code == 401
    
    def test_get_me_authenticated(self):
        """Test GET /api/auth/me with valid token"""
        # Signup and get token
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "dob": self.adult_dob,
            "display_name": f"Test User {self.unique_id}",
            "handle": self.test_handle
        }
        signup_response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        token = signup_response.json()["access_token"]
        
        # Get me
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == self.test_email
        assert data["handle"] == self.test_handle.lower()
    
    def test_get_me_unauthenticated(self):
        """Test GET /api/auth/me without token fails"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


class TestProfiles:
    """Profile endpoint tests"""
    
    @pytest.fixture
    def authenticated_user(self):
        """Create and authenticate a test user"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"{TEST_PREFIX}profile_{unique_id}@cliqup.com"
        handle = f"{TEST_PREFIX}profile{unique_id}"
        adult_dob = (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d")
        
        payload = {
            "email": email,
            "password": "testpass123",
            "dob": adult_dob,
            "display_name": f"Profile User {unique_id}",
            "handle": handle
        }
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        data = response.json()
        return {
            "token": data["access_token"],
            "user_id": data["user"]["id"],
            "headers": {"Authorization": f"Bearer {data['access_token']}"}
        }
    
    def test_get_my_profile(self, authenticated_user):
        """Test GET /api/profiles/me"""
        response = requests.get(
            f"{BASE_URL}/api/profiles/me",
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "handle" in data
        assert "display_name" in data
    
    def test_update_my_profile(self, authenticated_user):
        """Test PUT /api/profiles/me"""
        update_payload = {
            "bio": "Updated bio for testing",
            "interests": ["music", "sports"]
        }
        response = requests.put(
            f"{BASE_URL}/api/profiles/me",
            headers=authenticated_user["headers"],
            json=update_payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["bio"] == "Updated bio for testing"
        
        # Verify persistence with GET
        get_response = requests.get(
            f"{BASE_URL}/api/profiles/me",
            headers=authenticated_user["headers"]
        )
        assert get_response.json()["bio"] == "Updated bio for testing"
    
    def test_follow_user(self, authenticated_user):
        """Test POST /api/profiles/{user_id}/follow"""
        # Create another user to follow
        unique_id = str(uuid.uuid4())[:8]
        other_payload = {
            "email": f"{TEST_PREFIX}follow_{unique_id}@cliqup.com",
            "password": "testpass123",
            "dob": (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d"),
            "display_name": f"Follow Target {unique_id}",
            "handle": f"{TEST_PREFIX}follow{unique_id}"
        }
        other_response = requests.post(f"{BASE_URL}/api/auth/signup", json=other_payload)
        other_user_id = other_response.json()["user"]["id"]
        
        # Follow the user
        response = requests.post(
            f"{BASE_URL}/api/profiles/{other_user_id}/follow",
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["following"] == True
    
    def test_unfollow_user(self, authenticated_user):
        """Test DELETE /api/profiles/{user_id}/follow"""
        # Create another user
        unique_id = str(uuid.uuid4())[:8]
        other_payload = {
            "email": f"{TEST_PREFIX}unfollow_{unique_id}@cliqup.com",
            "password": "testpass123",
            "dob": (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d"),
            "display_name": f"Unfollow Target {unique_id}",
            "handle": f"{TEST_PREFIX}unfollow{unique_id}"
        }
        other_response = requests.post(f"{BASE_URL}/api/auth/signup", json=other_payload)
        other_user_id = other_response.json()["user"]["id"]
        
        # Follow first
        requests.post(
            f"{BASE_URL}/api/profiles/{other_user_id}/follow",
            headers=authenticated_user["headers"]
        )
        
        # Then unfollow
        response = requests.delete(
            f"{BASE_URL}/api/profiles/{other_user_id}/follow",
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["following"] == False


class TestMeetDating:
    """Meet/Dating feature tests"""
    
    @pytest.fixture
    def adult_user(self):
        """Create an adult user for Meet testing"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"{TEST_PREFIX}meet_{unique_id}@cliqup.com"
        handle = f"{TEST_PREFIX}meet{unique_id}"
        adult_dob = (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d")
        
        payload = {
            "email": email,
            "password": "testpass123",
            "dob": adult_dob,
            "display_name": f"Meet User {unique_id}",
            "handle": handle
        }
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        data = response.json()
        return {
            "token": data["access_token"],
            "user_id": data["user"]["id"],
            "headers": {"Authorization": f"Bearer {data['access_token']}"}
        }
    
    @pytest.fixture
    def teen_user(self):
        """Create a teen user for Meet testing"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"{TEST_PREFIX}teen_{unique_id}@cliqup.com"
        handle = f"{TEST_PREFIX}teen{unique_id}"
        teen_dob = (datetime.now() - timedelta(days=365*16)).strftime("%Y-%m-%d")
        
        payload = {
            "email": email,
            "password": "testpass123",
            "dob": teen_dob,
            "display_name": f"Teen User {unique_id}",
            "handle": handle
        }
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        data = response.json()
        return {
            "token": data["access_token"],
            "user_id": data["user"]["id"],
            "headers": {"Authorization": f"Bearer {data['access_token']}"}
        }
    
    def test_meet_status_adult_not_verified(self, adult_user):
        """Test GET /api/meet/status for adult without age verification"""
        response = requests.get(
            f"{BASE_URL}/api/meet/status",
            headers=adult_user["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meet_locked"] == True
        assert data["age_assured_18plus"] == False
    
    def test_meet_status_teen_blocked(self, teen_user):
        """Test GET /api/meet/status for teen user (should be blocked)"""
        response = requests.get(
            f"{BASE_URL}/api/meet/status",
            headers=teen_user["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meet_locked"] == True
        assert "18+" in data["reason"]
    
    def test_age_assure_adult(self, adult_user):
        """Test POST /api/meet/age-assure for adult"""
        response = requests.post(
            f"{BASE_URL}/api/meet/age-assure",
            headers=adult_user["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["age_assured_18plus"] == True
        assert data["meet_enabled"] == True
        
        # Verify status changed
        status_response = requests.get(
            f"{BASE_URL}/api/meet/status",
            headers=adult_user["headers"]
        )
        assert status_response.json()["meet_locked"] == False
    
    def test_age_assure_teen_blocked(self, teen_user):
        """Test POST /api/meet/age-assure for teen (should fail)"""
        response = requests.post(
            f"{BASE_URL}/api/meet/age-assure",
            headers=teen_user["headers"]
        )
        assert response.status_code == 403
    
    def test_create_squad(self, adult_user):
        """Test POST /api/meet/squads"""
        # First verify age
        requests.post(f"{BASE_URL}/api/meet/age-assure", headers=adult_user["headers"])
        
        squad_payload = {
            "name": f"Test Squad {str(uuid.uuid4())[:8]}",
            "visibility": "public",
            "veto_enabled": False
        }
        response = requests.post(
            f"{BASE_URL}/api/meet/squads",
            headers=adult_user["headers"],
            json=squad_payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == squad_payload["name"]
        assert data["owner_id"] == adult_user["user_id"]
        assert data["member_count"] == 1
        assert "squad_elo" in data
    
    def test_get_my_squads(self, adult_user):
        """Test GET /api/meet/squads"""
        # First verify age and create a squad
        requests.post(f"{BASE_URL}/api/meet/age-assure", headers=adult_user["headers"])
        
        squad_payload = {
            "name": f"My Squad {str(uuid.uuid4())[:8]}",
            "visibility": "public",
            "veto_enabled": False
        }
        requests.post(
            f"{BASE_URL}/api/meet/squads",
            headers=adult_user["headers"],
            json=squad_payload
        )
        
        # Get squads
        response = requests.get(
            f"{BASE_URL}/api/meet/squads",
            headers=adult_user["headers"]
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_invite_to_squad(self, adult_user):
        """Test POST /api/meet/squads/{id}/invite"""
        # Verify age
        requests.post(f"{BASE_URL}/api/meet/age-assure", headers=adult_user["headers"])
        
        # Create squad
        squad_response = requests.post(
            f"{BASE_URL}/api/meet/squads",
            headers=adult_user["headers"],
            json={"name": f"Invite Squad {str(uuid.uuid4())[:8]}", "visibility": "public", "veto_enabled": False}
        )
        squad_id = squad_response.json()["id"]
        
        # Create another user to invite
        unique_id = str(uuid.uuid4())[:8]
        other_payload = {
            "email": f"{TEST_PREFIX}invitee_{unique_id}@cliqup.com",
            "password": "testpass123",
            "dob": (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d"),
            "display_name": f"Invitee {unique_id}",
            "handle": f"{TEST_PREFIX}invitee{unique_id}"
        }
        other_response = requests.post(f"{BASE_URL}/api/auth/signup", json=other_payload)
        invitee_id = other_response.json()["user"]["id"]
        
        # Invite
        response = requests.post(
            f"{BASE_URL}/api/meet/squads/{squad_id}/invite",
            headers=adult_user["headers"],
            json={"invitee_id": invitee_id}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["invitee_id"] == invitee_id
        assert data["status"] == "pending"
    
    def test_discover_squads(self, adult_user):
        """Test GET /api/meet/discover"""
        # Verify age
        requests.post(f"{BASE_URL}/api/meet/age-assure", headers=adult_user["headers"])
        
        response = requests.get(
            f"{BASE_URL}/api/meet/discover",
            headers=adult_user["headers"]
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Each squad should have compatibility_score
        for squad in data:
            assert "compatibility_score" in squad
            assert "squad_elo" in squad
    
    def test_get_matches(self, adult_user):
        """Test GET /api/meet/matches"""
        # Verify age
        requests.post(f"{BASE_URL}/api/meet/age-assure", headers=adult_user["headers"])
        
        response = requests.get(
            f"{BASE_URL}/api/meet/matches",
            headers=adult_user["headers"]
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestSocial:
    """Social features (posts, feed) tests"""
    
    @pytest.fixture
    def authenticated_user(self):
        """Create and authenticate a test user"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"{TEST_PREFIX}social_{unique_id}@cliqup.com"
        handle = f"{TEST_PREFIX}social{unique_id}"
        adult_dob = (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d")
        
        payload = {
            "email": email,
            "password": "testpass123",
            "dob": adult_dob,
            "display_name": f"Social User {unique_id}",
            "handle": handle
        }
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        data = response.json()
        return {
            "token": data["access_token"],
            "user_id": data["user"]["id"],
            "headers": {"Authorization": f"Bearer {data['access_token']}"}
        }
    
    def test_create_post(self, authenticated_user):
        """Test POST /api/posts"""
        post_payload = {
            "content": f"Test post content {str(uuid.uuid4())[:8]}",
            "media_urls": []
        }
        response = requests.post(
            f"{BASE_URL}/api/posts",
            headers=authenticated_user["headers"],
            json=post_payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == post_payload["content"]
        assert data["user_id"] == authenticated_user["user_id"]
        assert "id" in data
    
    def test_get_feed(self, authenticated_user):
        """Test GET /api/posts/feed"""
        response = requests.get(
            f"{BASE_URL}/api/posts/feed",
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_explore(self, authenticated_user):
        """Test GET /api/posts/explore"""
        response = requests.get(
            f"{BASE_URL}/api/posts/explore",
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_react_to_post(self, authenticated_user):
        """Test POST /api/posts/{id}/react"""
        # Create a post first
        post_response = requests.post(
            f"{BASE_URL}/api/posts",
            headers=authenticated_user["headers"],
            json={"content": "Post to react to", "media_urls": []}
        )
        post_id = post_response.json()["id"]
        
        # React to it
        response = requests.post(
            f"{BASE_URL}/api/posts/{post_id}/react",
            headers=authenticated_user["headers"],
            json={"reaction_type": "like"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["reacted"] == True


class TestMessaging:
    """Messaging endpoint tests"""
    
    @pytest.fixture
    def authenticated_user(self):
        """Create and authenticate a test user"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"{TEST_PREFIX}msg_{unique_id}@cliqup.com"
        handle = f"{TEST_PREFIX}msg{unique_id}"
        adult_dob = (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d")
        
        payload = {
            "email": email,
            "password": "testpass123",
            "dob": adult_dob,
            "display_name": f"Msg User {unique_id}",
            "handle": handle
        }
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        data = response.json()
        return {
            "token": data["access_token"],
            "user_id": data["user"]["id"],
            "headers": {"Authorization": f"Bearer {data['access_token']}"}
        }
    
    def test_get_conversations(self, authenticated_user):
        """Test GET /api/conversations"""
        response = requests.get(
            f"{BASE_URL}/api/conversations",
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_dm(self, authenticated_user):
        """Test POST /api/conversations/dm/{user_id}"""
        # Create another user
        unique_id = str(uuid.uuid4())[:8]
        other_payload = {
            "email": f"{TEST_PREFIX}dm_{unique_id}@cliqup.com",
            "password": "testpass123",
            "dob": (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d"),
            "display_name": f"DM Target {unique_id}",
            "handle": f"{TEST_PREFIX}dm{unique_id}"
        }
        other_response = requests.post(f"{BASE_URL}/api/auth/signup", json=other_payload)
        other_user_id = other_response.json()["user"]["id"]
        
        # Create DM
        response = requests.post(
            f"{BASE_URL}/api/conversations/dm/{other_user_id}",
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["type"] == "dm"
    
    def test_send_message(self, authenticated_user):
        """Test POST /api/conversations/{id}/messages"""
        # Create another user and DM
        unique_id = str(uuid.uuid4())[:8]
        other_payload = {
            "email": f"{TEST_PREFIX}sendmsg_{unique_id}@cliqup.com",
            "password": "testpass123",
            "dob": (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d"),
            "display_name": f"Send Msg Target {unique_id}",
            "handle": f"{TEST_PREFIX}sendmsg{unique_id}"
        }
        other_response = requests.post(f"{BASE_URL}/api/auth/signup", json=other_payload)
        other_user_id = other_response.json()["user"]["id"]
        
        # Create DM
        dm_response = requests.post(
            f"{BASE_URL}/api/conversations/dm/{other_user_id}",
            headers=authenticated_user["headers"]
        )
        conversation_id = dm_response.json()["id"]
        
        # Send message
        response = requests.post(
            f"{BASE_URL}/api/conversations/{conversation_id}/messages",
            headers=authenticated_user["headers"],
            json={"content": "Hello, this is a test message!"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == "Hello, this is a test message!"
        assert data["sender_id"] == authenticated_user["user_id"]


class TestNotifications:
    """Notification endpoint tests"""
    
    @pytest.fixture
    def authenticated_user(self):
        """Create and authenticate a test user"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"{TEST_PREFIX}notif_{unique_id}@cliqup.com"
        handle = f"{TEST_PREFIX}notif{unique_id}"
        adult_dob = (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d")
        
        payload = {
            "email": email,
            "password": "testpass123",
            "dob": adult_dob,
            "display_name": f"Notif User {unique_id}",
            "handle": handle
        }
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        data = response.json()
        return {
            "token": data["access_token"],
            "user_id": data["user"]["id"],
            "headers": {"Authorization": f"Bearer {data['access_token']}"}
        }
    
    def test_get_notifications(self, authenticated_user):
        """Test GET /api/notifications"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_unread_count(self, authenticated_user):
        """Test GET /api/notifications/unread-count"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
