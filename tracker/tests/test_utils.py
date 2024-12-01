import django

django.setup()

from asgiref.sync import async_to_sync
from django.test import TestCase
from faker import Faker

from tracker.choices import Roles
from tracker.models import CustomUser, Repository, TelegramUser
from tracker.utils import get_all_repostitories, get_user
from unittest.mock import patch, Mock
from tracker.utils import check_issue_assignment_events
import requests


fake = Faker()

telagram_id = fake.random_int(min=100000000, max=9999999999)


class TestGetAllRepositories(TestCase):
    def setUp(self):
        self.custom_user = CustomUser.objects.create(
            email=fake.email, role=Roles.CONTRIBUTOR
        )

        self.user = TelegramUser.objects.create(
            telegram_id=telagram_id, user_id=self.custom_user.id
        )

        self.repo1 = Repository.objects.create(user=self.custom_user, name="TestRepo1")
        self.repo2 = Repository.objects.create(user=self.custom_user, name="TestRepo2")

    def test_get_all_repositories_valid_user(self):
        """Test valid telegram ID fetching repositories."""
        result = async_to_sync(get_all_repostitories)(tele_id=telagram_id)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "TestRepo1")
        self.assertEqual(result[1]["name"], "TestRepo2")

    def test_get_all_repositories_invalid_user(self):
        """Test invalid telegram ID raises exception."""
        with self.assertRaises(TelegramUser.DoesNotExist):
            async_to_sync(get_all_repostitories)(tele_id="987654321")


class TestGetUser(TestCase):
    def setUp(self):
        """Set up test data."""
        self.custom_user = CustomUser.objects.create(
            email=fake.email(),
            role=Roles.CONTRIBUTOR
        )
        self.user_id = str(self.custom_user.id)

    def test_get_user_valid_uuid(self):
        """Test retrieving user with valid UUID."""
        result = async_to_sync(get_user)(uuid=self.user_id)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.custom_user)

    def test_get_user_invalid_uuid(self):
        """Test retrieving user with invalid UUID raises exception."""
        invalid_uuid = "00000000-0000-0000-0000-000000000000"
        with self.assertRaises(CustomUser.DoesNotExist):
            async_to_sync(get_user)(uuid=invalid_uuid)

class TestCheckIssueAssignmentEvents(TestCase):
    def setUp(self):
        """Set up test data."""
        self.issue = {
            "events_url": "https://api.github.com/repos/owner/repo/issues/1/events"
        }
        
    @patch('requests.get')
    def test_successful_assignment_event(self, mock_get):
        """Test successful retrieval of assignment event."""
        # Mock response data
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "event": "assigned",
                "assignee": {"login": "testuser"},
                "created_at": "2024-01-01T12:00:00Z"
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = check_issue_assignment_events(self.issue)
        
        self.assertEqual(result["assignee"], "testuser")
        self.assertEqual(result["assigned_at"], "2024-01-01T12:00:00Z")
        mock_get.assert_called_once_with(
            self.issue["events_url"],
            headers=patch.dict('tracker.utils.HEADERS', {})
        )

    @patch('requests.get')
    def test_multiple_assignment_events(self, mock_get):
        """Test that only the last assignment event is returned."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "event": "assigned",
                "assignee": {"login": "user1"},
                "created_at": "2024-01-01T12:00:00Z"
            },
            {
                "event": "assigned",
                "assignee": {"login": "user2"},
                "created_at": "2024-01-02T12:00:00Z"
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = check_issue_assignment_events(self.issue)
        
        self.assertEqual(result["assignee"], "user2")
        self.assertEqual(result["assigned_at"], "2024-01-02T12:00:00Z")

    @patch('requests.get')
    def test_no_assignment_events(self, mock_get):
        """Test when there are no assignment events."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "event": "labeled",
                "label": {"name": "bug"}
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = check_issue_assignment_events(self.issue)
        
        self.assertEqual(result, {"assignee": "", "assigned_at": ""})

    @patch('requests.get')
    def test_request_exception(self, mock_get):
        """Test handling of request exceptions."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = check_issue_assignment_events(self.issue)
        
        self.assertEqual(result, {})

    @patch('requests.get')
    def test_missing_events_url(self, mock_get):
        """Test handling of missing events_url."""
        issue_without_url = {}
        
        result = check_issue_assignment_events(issue_without_url)
        
        self.assertEqual(result, {})
        mock_get.assert_called_once_with("", headers=patch.dict('tracker.utils.HEADERS', {}))

    @patch('requests.get')
    def test_malformed_response(self, mock_get):
        """Test handling of malformed response data."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "event": "assigned",
                # Missing assignee and created_at fields
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = check_issue_assignment_events(self.issue)
        
        self.assertEqual(result["assignee"], "")
        self.assertEqual(result["assigned_at"], "")