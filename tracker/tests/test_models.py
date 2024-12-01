import django
django.setup()

from django.test import TestCase
from django.core.exceptions import ValidationError
from faker import Faker

from tracker.models import CustomUser
from tracker.choices import Roles

fake = Faker()

class TestCustomUserManager(TestCase):
    def setUp(self):
        """Set up test data."""
        self.email = fake.email()
        self.password = fake.password()
        self.role = Roles.CONTRIBUTOR

    def test_create_user(self):
        """Test creating a regular user."""
        user = CustomUser.objects.create_user(
            email=self.email,
            password=self.password,
            role=self.role
        )
        
        self.assertEqual(user.email, self.email)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_admin)
        self.assertEqual(user.role, self.role)
        self.assertTrue(user.check_password(self.password))
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Test creating a superuser."""
        superuser = CustomUser.objects.create_superuser(
            email=self.email,
            password=self.password,
            role=self.role
        )
        
        self.assertEqual(superuser.email, self.email)
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_admin)
        self.assertEqual(superuser.role, self.role)
        self.assertTrue(superuser.check_password(self.password))
        self.assertTrue(superuser.is_staff)

    def test_create_user_with_invalid_email(self):
        """Test creating a user with invalid email format."""
        invalid_email = "invalid.email@format"
        
        with self.assertRaises(ValueError) as context:
            CustomUser.objects.create_user(
                email=invalid_email,
                password=self.password,
                role=self.role
            )
        
        self.assertEqual(str(context.exception), "Invalid email format")

    def test_create_user_without_role(self):
        """Test creating a user without specifying a role."""
        user = CustomUser.objects.create_user(
            email=self.email,
            password=self.password
        )
        
        self.assertEqual(user.role, Roles.CONTRIBUTOR)

class TestCustomUser(TestCase):
    def setUp(self):
        """Set up test data."""
        self.email = fake.email()
        self.password = fake.password()
        self.user = CustomUser.objects.create_user(
            email=self.email,
            password=self.password
        )

    def test_str_representation(self):
        """Test the string representation of the user."""
        self.assertEqual(str(self.user), self.email)

    def test_has_perm(self):
        """Test the has_perm method."""
        self.assertTrue(self.user.has_perm('some_permission'))
        self.assertTrue(self.user.has_perm('some_permission', obj=None))

    def test_has_module_perms(self):
        """Test the has_module_perms method."""
        self.assertTrue(self.user.has_module_perms('some_app'))

    def test_is_staff_property(self):
        """Test the is_staff property."""
        self.assertFalse(self.user.is_staff)
        self.user.is_admin = True
        self.user.save()
        self.assertTrue(self.user.is_staff)

    def test_is_project_lead(self):
        """Test the is_project_lead method."""
        self.assertFalse(self.user.is_project_lead())
        
        self.user.role = Roles.PROJECT_LEAD
        self.user.save()
        self.assertTrue(self.user.is_project_lead())

    def test_email_uniqueness(self):
        """Test that users cannot be created with duplicate emails."""
        with self.assertRaises(Exception):
            CustomUser.objects.create_user(
                email=self.email,
                password=self.password
            )

    def test_email_case_sensitivity(self):
        """Test that email normalization works correctly."""
        upper_email = self.email.upper()
        with self.assertRaises(Exception):
            CustomUser.objects.create_user(
                email=upper_email,
                password=self.password
            )