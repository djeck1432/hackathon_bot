from django.db import models


class Roles(models.TextChoices):
    """
    The roles class adds a role to members on a project.

    The choices include project lead and contributors.

    Attributes:
        project_lead (Role Enumeration): Project Lead Enumeration Variant.
        contributor (Role Enumertion): Contributor Enumeration Variant.
    """

    PROJECT_LEAD = "lead", "Tech-lead"
    CONTRIBUTOR = "contributor", "Contributor"
