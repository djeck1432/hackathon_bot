import asyncio

from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.utils.html import format_html
from django.utils.safestring import SafeString
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SolarSchedule,
)

from .choices import Roles
from .bases import PredefinedUserAdminBase
from .models import Contributor, Repository, Support, CustomUser
from .telegram.bot import create_tg_link

admin.site.unregister(Group)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(PeriodicTask)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)


@admin.register(Repository)
class RepositoryAdmin(PredefinedUserAdminBase):
    """
    Custom Django admin class to manage Repository objects.

    This class customizes the Django admin interface for Repository models,
    providing specific configurations like setting default user properties
    and generating a referral link for each repository.

    Methods:
        telegram_link: Adds a referral link to display in the list view.
        get_queryset: Filters the queryset to show only the current user's repositories.

    Attributes:
        list_display (tuple): Fields to be displayed in the list view of the admin panel.
    """

    list_display = ("name", "author", "telegram_link")

    def telegram_link(self, obj) -> SafeString:
        """
        A function that adds referal link to object's display list
        :param obj:
        :return: SafeString
        """

        link = asyncio.run(create_tg_link(obj.user.id))

        return format_html(
            '<a href="{}" target="_blank">Get info about repository</a>', link
        )

    def get_queryset(self, request) -> QuerySet:
        """
        A custom method that returns the queryset filtered by the current user.
        :param request: HttpRequest
        :return: QuerySet
        """
        queryset = super().get_queryset(request)

        return queryset.filter(user=request.user)


@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):
    """
    Admin class to manage contributors with role-based visibility.

    Methods:
        get_queryset: Filters contributors based on the role of the logged-in user.
        changelist_view: Returns JSON data if requested, otherwise renders admin UI.
        has_module_permission: Displays the model only for project leads.
    """

    list_display = ("user", "role", "rank", "notes")

    def has_module_permission(self, request) -> bool:
        """
        Displays the model only for project leads.
        :param request: HttpRequest
        :return: bool
        """
        user = request.user

        if user.is_authenticated:
            return user.role == Roles.PROJECT_LEAD

        return False

    def get_form(self, request, obj=None, **kwargs) -> BaseModelForm:
        """
        Customizes the model form to set the user field to the current user.
        :param request: HttpRequest
        :param obj: AbstractModel
        :param kwargs: dict
        :return: BaseModelForm
        """
        form = super().get_form(request, obj, **kwargs)

        form.base_fields["role"].initial = Roles.CONTRIBUTOR
        form.base_fields["role"].disabled = True
        form.base_fields["user"].queryset = CustomUser.objects.filter(role=Roles.CONTRIBUTOR)

        return form


@admin.register(Support)
class SupportAdmin(PredefinedUserAdminBase):
    """
    A class to manage Support objects that inherits PredefinedUserAdminBase class.

    Methods:
        has_module_permissions: Displays the model only for project leads.
        get_form: Customizes the model form to set the repository field to the current user's repositories.
    """

    def has_module_permission(self, request) -> bool:
        """
        Displays the model only for project leads.
        :param request: HttpRequest
        :return: bool
        """
        user = request.user

        if user.is_authenticated:
            return user.role == Roles.PROJECT_LEAD

        return False

    def get_form(self, request, obj=None, **kwargs) -> BaseModelForm:
        form = super().get_form(request, obj, **kwargs)

        form.base_fields["repository"].queryset = Repository.objects.filter(user=request.user)

        return form
