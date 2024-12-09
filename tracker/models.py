import requests
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from shared.models import AbstractModel
from tracker.choices import Roles
from tracker.values import ROLE_MAX_CHARACTER_LENGTH, DefaultModelValues


class CustomUserManager(BaseUserManager):
    """
    A custom manager for CustomUser, providing methods to create users and superusers.

    Methods:
    - create_user: Creates and returns a new user with the given email and password.
    - create_superuser: Creates and returns a new superuser with the given email and password.
    """

    def create_user(
        self, email: str = None, password: str = None, role: str = None
    ) -> "CustomUser":
        """
        Creates a new user
        :param email: str
        :param password: str
        :param role: str = None
        :return: CustomUser
        """
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise ValueError("Invalid email format")

        if not role:
            role = Roles.CONTRIBUTOR

        user = self.model(
            email=self.normalize_email(email),
            password=password,
            role=role,
        )

        user.is_active = True
        user.is_admin = False
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self, email: str = None, password: str = None, role: str = None
    ) -> "CustomUser":
        """
        Creates a new superuser
        :param email: str
        :param password: str
        :param role: str = None
        :return: CustomUser
        """
        user = self.create_user(email, password, role)

        user.is_admin = True
        user.save(update_fields=["is_admin", "is_active"])

        return user


class CustomUser(AbstractModel, AbstractBaseUser):
    """
    A model representing a custom user with email as the unique identifier.

    Attributes:
    - email (EmailField): The email of the user which is unique and serves as the username.
    - role (CharField): The role of the user which is either contributor or lead.
    - is_active (BooleanField): Indicates whether the user is active. Default is True.
    - is_admin (BooleanField): Indicates whether the user is an admin. Default is False.

    Methods:
    - __str__: Returns a string representation of the user, which is the email of the user.
    - has_perm: A stub method to always return True. This can be customized for permission logic.
    - has_module_perms: A stub method to always return True. This can be customized for module permission logic.
    - is_staff: A property that returns True if the user is an admin.
    """

    email = models.EmailField(
        max_length=DefaultModelValues.email_max_length, unique=True
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    role = models.CharField(
        max_length=ROLE_MAX_CHARACTER_LENGTH,
        choices=Roles.choices,
        default=Roles.CONTRIBUTOR,
    )
    USERNAME_FIELD = "email"

    objects = CustomUserManager()

    def __str__(self) -> str:
        """
        Returns a string representation of the user, which is the email of the user.
        :return: str
        """
        return f"{self.email}"

    @staticmethod
    def has_perm(perm, obj=None) -> bool:
        """
        Stub method to always return True. This can be customized to check for specific permissions.
        :param perm: The permission being checked.
        :param obj: The object for which perm is checked.
        :return: bool
        """
        return True

    @staticmethod
    def has_module_perms(app_label) -> bool:
        """
        Stub method to always return True. This can be customized to check for specific module permissions.
        :param app_label: The label of the app for which permissions are checked.
        :return: bool
        """
        return True

    @property
    def is_staff(self) -> models.BooleanField:
        """
        Property that returns True if the user is an admin.
        :return: bool
        """
        return self.is_admin

    def is_project_lead(self) -> bool:
        """
        Checks if the user is a project lead
        :return: bool
        """
        return self.role == Roles.PROJECT_LEAD


class Repository(AbstractModel):
    """
    A model representing a repository, including its name, author, and link.

    Attributes:
    - name (CharField): The name of the repository with a max length defined by DefaultModelValues.
    - author (CharField): The author of the repository with a max length defined by DefaultModelValues.
    - link (URLField): A URL to the repository with a max length defined by DefaultModelValues.
    - time_limit (PositiveIntegerField): The time limit associated with the repository in seconds.

    Inherits from:
    - AbstractModel: A shared abstract model providing common fields or methods.

    Methods:
    - __str__: Returns a string representation of the repository in the format 'author/name'.
    """

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=DefaultModelValues.name_max_length)
    author = models.CharField(max_length=DefaultModelValues.author_max_length)
    link = models.URLField(max_length=DefaultModelValues.link_max_length)
    time_limit = models.PositiveIntegerField(
        default=DefaultModelValues.time_limit_default
    )

    class Meta:
        verbose_name_plural = "Repositories"

    def clean(self) -> None:
        """
        Validates all repository fields.
        :return: None
        """
        super().clean()

        if self.name not in self.link:
            raise ValidationError("Repository name must be in the link.")

        if self.author not in self.link:
            raise ValidationError("Repository author must be in the link.")

        try:
            response = requests.get(str(self.link))
            response.raise_for_status()

            if not response.ok:
                raise ValidationError("Repository link is invalid.")

        except requests.exceptions.RequestException as e:
            raise ValidationError(f"Something went wrong: {e}")

    def __str__(self) -> str:
        """
        Returns a string representation of the repository in the format 'author/name'.
        :return: str
        """
        return f"{self.author}/{self.name}"

    def save(self, *args, **kwargs) -> None:
        repository = super().save(*args, **kwargs)

        Support.objects.create(repository=repository)


class TelegramUser(AbstractModel):
    """
    Represents a Telegram user associated with a custom user in the system.

    Attributes:
        user (CustomUser): A one-to-one relationship with the CustomUser model.
        telegram_id (str): A unique identifier for the user on Telegram.

    Methods:
    - __str__: Returns a string representation of the telegram user.
    """

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    telegram_id = models.CharField(unique=True)

    def __str__(self) -> str:
        """
        Returns a string representation of the TelegramUser instance.
        :return: str
        """
        return f"{self.user}: {self.telegram_id}"

    def create_approval_task(
        self, interval: int = settings.DEFAULT_SCHEDULE_INTERVAL
    ) -> "PeriodicTask":
        """
        Creates a periodic task for fetching user approval and revision.
        :param interval: The interval for the task (default: 1 hour)

        :return: PeriodicTask
        """
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=interval, period=IntervalSchedule.SECONDS
        )
        task, _ = PeriodicTask.objects.get_or_create(
            name=f"user_{self.user.id}_approval_task",
            task="core.tasks.fetch_approvals",
            interval=schedule,
            args=[str(self.telegram_id)],
        )
        return task


class Contributor(AbstractModel):
    """
    Representes a contributor with specific details and metadata

    Attributes:
    - user (CustomUser): A ForeignKey to the CustomUser model.
    - role (str): The role of the contributor.
    - notes (str): Notes for contributors, visible only to project leads.
    - rank (int): A ranking for the contributor, also only visible to project leads.
    """

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="contributors"
    )
    role = models.CharField(
        max_length=ROLE_MAX_CHARACTER_LENGTH,
        choices=Roles.choices,
        default=Roles.CONTRIBUTOR,
    )
    notes = models.TextField(blank=True, null=True)
    rank = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Contributors"

    def __str__(self):
        """
        Returns a string representation of the contributor, including the telegram_id from the related TelegramUser.
        """
        telegram_id = (
            self.user.telegramuser.telegram_id
            if hasattr(self.user, "telegramuser")
            else "No Telegram ID"
        )
        return f"Contributor: {telegram_id} (Role: {self.role})"


class Support(AbstractModel):
    """
    Represents a support request from a user via Telegram.

    Attributes:
        user (CustomUser): Foreign key relationship with the CustomUser model.
        telegram_username (str): The Telegram username of the user requesting support.
    """

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    telegram_username = models.CharField(max_length=DefaultModelValues.name_max_length)

    def __str__(self) -> str:
        """
        Returns a string representation of the Support instance.
        :return: str
        """
        if self.telegram_username.startswith("@"):
            return f"{self.telegram_username}"
        return f"@{self.telegram_username}"
