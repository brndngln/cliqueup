#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class NexusAPITester:
    def __init__(self, base_url="https://squad-dating.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Response: {response.text[:100]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {}
            return None

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return None

    def test_login(self):
        """Test login with existing test account"""
        print("\n🔐 Testing Authentication...")
        
        response_data = self.run_test(
            "Login with test account",
            "POST",
            "auth/login",
            200,
            data={"email": "test@nexus.com", "password": "password123"}
        )
        
        if response_data and 'access_token' in response_data:
            self.token = response_data['access_token']
            self.user_id = response_data['user']['id']
            return True
        return False

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        # Test /auth/me
        me_data = self.run_test(
            "Get current user info",
            "GET",
            "auth/me",
            200
        )
        
        if me_data:
            print(f"   User: {me_data.get('display_name')} (@{me_data.get('handle')})")
            print(f"   Age Band: {me_data.get('age_band')}")

    def test_profile_endpoints(self):
        """Test profile management"""
        print("\n👤 Testing Profile Management...")
        
        # Get my profile
        profile_data = self.run_test(
            "Get my profile",
            "GET",
            "profiles/me",
            200
        )
        
        if profile_data:
            print(f"   Profile: {profile_data.get('display_name')} - {profile_data.get('bio', 'No bio')}")

        # Update profile
        update_data = {
            "bio": f"Updated bio at {datetime.now().strftime('%H:%M:%S')}"
        }
        
        self.run_test(
            "Update profile",
            "PUT",
            "profiles/me",
            200,
            data=update_data
        )

    def test_meet_endpoints(self):
        """Test Meet (dating) functionality"""
        print("\n💕 Testing Meet Features...")
        
        # Check meet status
        meet_status = self.run_test(
            "Get meet status",
            "GET",
            "meet/status",
            200
        )
        
        if meet_status:
            print(f"   Meet Locked: {meet_status.get('meet_locked')}")
            print(f"   Age Assured: {meet_status.get('age_assured_18plus')}")
            
            # If not age assured, try to age assure
            if not meet_status.get('age_assured_18plus'):
                self.run_test(
                    "Age assure for Meet",
                    "POST",
                    "meet/age-assure",
                    200
                )

        # Get squads
        squads_data = self.run_test(
            "Get my squads",
            "GET",
            "meet/squads",
            200
        )
        
        if squads_data:
            print(f"   Found {len(squads_data)} squads")
            
        # Get matches
        matches_data = self.run_test(
            "Get matches",
            "GET",
            "meet/matches",
            200
        )
        
        if matches_data:
            print(f"   Found {len(matches_data)} matches")

        # Get discovery squads
        discovery_data = self.run_test(
            "Get discovery squads",
            "GET",
            "meet/discover",
            200
        )
        
        if discovery_data:
            print(f"   Found {len(discovery_data)} squads to discover")

    def test_posts_endpoints(self):
        """Test posts and feed functionality"""
        print("\n📝 Testing Posts & Feed...")
        
        # Create a test post
        post_data = {
            "type": "text",
            "content": f"Test post created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "tags": ["test", "api"]
        }
        
        created_post = self.run_test(
            "Create new post",
            "POST",
            "posts",
            200,
            data=post_data
        )
        
        if created_post:
            post_id = created_post.get('id')
            print(f"   Created post: {post_id}")
            
            # Get the post
            self.run_test(
                "Get created post",
                "GET",
                f"posts/{post_id}",
                200
            )
            
            # React to post
            self.run_test(
                "React to post",
                "POST",
                f"posts/{post_id}/react",
                200,
                data={"reaction_type": "like"}
            )

        # Get feed
        feed_data = self.run_test(
            "Get feed",
            "GET",
            "posts/feed",
            200
        )
        
        if feed_data:
            print(f"   Feed has {len(feed_data)} posts")

        # Get explore
        explore_data = self.run_test(
            "Get explore posts",
            "GET",
            "posts/explore",
            200
        )
        
        if explore_data:
            print(f"   Explore has {len(explore_data)} posts")

    def test_messaging_endpoints(self):
        """Test messaging functionality"""
        print("\n💬 Testing Messaging...")
        
        # Get conversations
        conversations_data = self.run_test(
            "Get conversations",
            "GET",
            "conversations",
            200
        )
        
        if conversations_data:
            print(f"   Found {len(conversations_data)} conversations")

    def test_notifications_endpoints(self):
        """Test notifications"""
        print("\n🔔 Testing Notifications...")
        
        # Get notifications
        notifications_data = self.run_test(
            "Get notifications",
            "GET",
            "notifications",
            200
        )
        
        if notifications_data:
            print(f"   Found {len(notifications_data)} notifications")

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting NEXUS API Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Login first
        if not self.test_login():
            print("❌ Login failed, stopping tests")
            return False
            
        # Run all test suites
        self.test_auth_endpoints()
        self.test_profile_endpoints()
        self.test_meet_endpoints()
        self.test_posts_endpoints()
        self.test_messaging_endpoints()
        self.test_notifications_endpoints()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = NexusAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/test_reports/backend_api_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': tester.tests_run,
            'passed_tests': tester.tests_passed,
            'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
            'results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())