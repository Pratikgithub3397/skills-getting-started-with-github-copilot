import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Basketball Team" in data
        assert "Chess Club" in data
        assert len(data) > 0

    def test_activities_have_required_fields(self):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self):
        """Test successful signup for an activity"""
        response = client.post("/activities/Tennis Club/signup?email=newstudent@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_invalid_activity(self):
        """Test signup for non-existent activity"""
        response = client.post("/activities/Nonexistent Activity/signup?email=student@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_registration(self):
        """Test that duplicate registration fails"""
        email = "duplicate@mergington.edu"
        # First signup should succeed
        response1 = client.post(f"/activities/Art Studio/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(f"/activities/Art Studio/signup?email={email}")
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_already_registered_student(self):
        """Test signup for student already in activity"""
        response = client.post("/activities/Basketball Team/signup?email=alex@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_successful_unregister(self):
        """Test successful unregistration from activity"""
        email = "unregister_test@mergington.edu"
        # First signup
        client.post(f"/activities/Drama Club/signup?email={email}")
        
        # Then unregister
        response = client.delete(f"/activities/Drama Club/unregister?email={email}")
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister from non-existent activity"""
        response = client.delete("/activities/Fake Activity/unregister?email=student@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_registered_student(self):
        """Test unregister for student not in activity"""
        response = client.delete("/activities/Chess Club/unregister?email=notregistered@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_signup_and_unregister_flow(self):
        """Test complete flow of signup and unregister"""
        email = "integration_test@mergington.edu"
        activity = "Science Club"
        
        # Check initial participant count
        activities_before = client.get("/activities").json()
        initial_count = len(activities_before[activity]["participants"])
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify participant was added
        activities_after_signup = client.get("/activities").json()
        after_signup_count = len(activities_after_signup[activity]["participants"])
        assert after_signup_count == initial_count + 1
        assert email in activities_after_signup[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify participant was removed
        activities_after_unregister = client.get("/activities").json()
        final_count = len(activities_after_unregister[activity]["participants"])
        assert final_count == initial_count
        assert email not in activities_after_unregister[activity]["participants"]

    def test_multiple_signups_same_activity(self):
        """Test multiple different students signing up for same activity"""
        activity = "Programming Class"
        email1 = "user1@mergington.edu"
        email2 = "user2@mergington.edu"
        
        # Sign up first user
        response1 = client.post(f"/activities/{activity}/signup?email={email1}")
        assert response1.status_code == 200
        
        # Sign up second user
        response2 = client.post(f"/activities/{activity}/signup?email={email2}")
        assert response2.status_code == 200
        
        # Verify both are registered
        activities = client.get("/activities").json()
        assert email1 in activities[activity]["participants"]
        assert email2 in activities[activity]["participants"]
