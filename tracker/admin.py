import asyncio

from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models import QuerySet
from django.http import JsonResponse
from django.utils.html import format_html
from django.utils.safestring import SafeString
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SolarSchedule,
)

from .bases import PredefinedUserAdminBase
from .models import Contributor, Repository, Support
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
    """

    list_display = ("user", "role", "rank", "notes")
    search_fields = ("user__email", "user__telegramuser__telegram_id", "role")
    list_filter = ("role",)

    def get_queryset(self, request) -> QuerySet:
        """
        Customize the queryset based on the user's role.
        Project leads can see all contributors; others see limited data.
        :param request: HttpRequest
        :return: QuerySet
        """
        queryset = super().get_queryset(request)

        if request.user.is_project_lead():
            return queryset
        return queryset.only("id", "user", "role")

    def changelist_view(self, request, extra_context=None):
        """
        Customize the change list view for contributors.
        Returns JSON data if requested via AJAX or API.
        """
        if request.headers.get("Content-Type") == "application/json":
            queryset = self.get_queryset(request)
            user = request.user

            if user.is_project_lead():
                data = [
                    {
                        "id": contributor.id,
                        "user": contributor.user.telegramuser.telegram_id,
                        "role": contributor.role,
                        "notes": contributor.notes,
                        "rank": contributor.rank,
                    }
                    for contributor in queryset
                ]
            else:
                data = [
                    {
                        "id": contributor.id,
                        "user": contributor.user.telegramuser.telegram_id,
                        "role": contributor.role,
                    }
                    for contributor in queryset
                ]

            return JsonResponse(data, safe=False)

        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Support)
class SupportAdmin(PredefinedUserAdminBase):
    """
    A class to manage Support objects that inherits PredefinedUserAdminBase class.
    """
