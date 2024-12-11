from unittest.mock import Mock, patch

import requests
from asgiref.sync import async_to_sync
from django.test import TestCase, TransactionTestCase
from faker import Faker

from tracker.choices import Roles
from tracker.models import CustomUser, Repository, TelegramUser
from tracker.utils import (
    check_issue_assignment_events,
    create_telegram_user,
    get_all_repostitories,
    get_user,
)

# TODO: move it to `values.py` in `tracker/tests`
fake = Faker()
# TODO: move it to `values.py` in `tracker/tests`
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
        result = async_to_sync(get_all_repostitories)(tele_id="987654321")

        self.assertEqual(len(result), 0)


class TestGetUser(TestCase):
    def setUp(self):
        """Set up test data."""
        self.custom_user = CustomUser.objects.create(
            email=fake.email(), role=Roles.CONTRIBUTOR
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
        self.issue_link = {
            "events_url": "https://api.github.com/repos/owner/repo/issues/1/events"
        }

    @patch("requests.get")
    def test_successful_assignment_event(self, mock_get):
        """Test successful retrieval of assignment event."""
        # Mock response data
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "event": "assigned",
                "assignee": {"login": "testuser"},
                "created_at": "2024-01-01T12:00:00Z",
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = check_issue_assignment_events(self.issue_link)

        self.assertEqual(result["assignee"], "testuser")
        self.assertEqual(result["assigned_at"], "2024-01-01T12:00:00Z")

    @patch("requests.get")
    def test_multiple_assignment_events(self, mock_get):
        """Test that only the last assignment event is returned."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "event": "assigned",
                "assignee": {"login": "user1"},
                "created_at": "2024-01-01T12:00:00Z",
            },
            {
                "event": "assigned",
                "assignee": {"login": "user2"},
                "created_at": "2024-01-02T12:00:00Z",
            },
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = check_issue_assignment_events(self.issue_link)

        self.assertEqual(result["assignee"], "user2")
        self.assertEqual(result["assigned_at"], "2024-01-02T12:00:00Z")

    @patch("requests.get")
    def test_no_assignment_events(self, mock_get):
        """Test when there are no assignment events."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"event": "labeled", "label": {"name": "bug"}}
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = check_issue_assignment_events(self.issue_link)

        self.assertEqual(result, {})

    @patch("requests.get")
    def test_request_exception(self, mock_get):
        """Test handling of request exceptions."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = check_issue_assignment_events(self.issue_link)

        self.assertEqual(result, {})

    @patch("requests.get")
    def test_missing_events_url(self, mock_get):
        """Test handling of missing events_url."""
        issue_without_url = {}

        result = check_issue_assignment_events(issue_without_url)

        self.assertEqual(result, {})


    @patch("requests.get")
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

        result = check_issue_assignment_events(self.issue_link)

        self.assertEqual(result["assignee"], "")
        self.assertEqual(result["assigned_at"], "")


class TestCreateTelegramUser(TransactionTestCase):
    def setUp(self):
        """Set up test data."""
        self.custom_user = CustomUser.objects.create(
            email=f"test_create_user_{fake.email()}", role=Roles.CONTRIBUTOR
        )
        self.telegram_id = str(fake.random_int(min=10000000000, max=99999999999))

    def tearDown(self):
        """Clean up after each test."""
        TelegramUser.objects.filter(user=self.custom_user).delete()
        self.custom_user.delete()

    def test_create_new_telegram_user(self):
        """Test creating a new telegram user when one doesn't exist."""
        TelegramUser.objects.filter(user=self.custom_user).delete()

        self.assertFalse(
            TelegramUser.objects.filter(
                telegram_id=self.telegram_id, user=self.custom_user
            ).exists()
        )

        async_to_sync(create_telegram_user)(self.custom_user, self.telegram_id)

        telegram_user = TelegramUser.objects.get(
            telegram_id=self.telegram_id, user=self.custom_user
        )
        self.assertIsNotNone(telegram_user)
        self.assertEqual(telegram_user.user, self.custom_user)
        self.assertEqual(telegram_user.telegram_id, self.telegram_id)

    def test_avoid_duplicate_telegram_user(self):
        """Test that no duplicate telegram user is created if one already exists."""
        TelegramUser.objects.filter(user=self.custom_user).delete()

        TelegramUser.objects.create(user=self.custom_user, telegram_id=self.telegram_id)

        initial_count = TelegramUser.objects.filter(
            telegram_id=self.telegram_id, user=self.custom_user
        ).count()

        async_to_sync(create_telegram_user)(self.custom_user, self.telegram_id)

        final_count = TelegramUser.objects.filter(
            telegram_id=self.telegram_id, user=self.custom_user
        ).count()
        self.assertEqual(initial_count, final_count)
        self.assertEqual(final_count, 1)

    def test_create_telegram_user_different_formats(self):
        """Test creating telegram users with different ID formats."""
        TelegramUser.objects.filter(user=self.custom_user).delete()

        test_ids = [
            "123456789",
            "0123456789",
            str(fake.random_int(min=10000000000, max=99999999999)),
        ]

        for test_id in test_ids:
            with self.subTest(telegram_id=test_id):

                TelegramUser.objects.filter(user=self.custom_user).delete()

                async_to_sync(create_telegram_user)(self.custom_user, test_id)

                telegram_user = TelegramUser.objects.get(
                    telegram_id=test_id, user=self.custom_user
                )
                self.assertIsNotNone(telegram_user)
