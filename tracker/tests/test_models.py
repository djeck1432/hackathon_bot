import django

django.setup()

from django.test import TestCase
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
