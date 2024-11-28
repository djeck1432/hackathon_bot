import asyncio

from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.utils.html import format_html
from django.utils.safestring import SafeString
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from .models import Repository
from .telegram.bot import create_tg_link

admin.site.unregister(Group)



@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    """
    Custom Django admin class to manage Repository objects.

    This class customizes the Django admin interface for Repository models,
    providing specific configurations like setting default user properties
    and generating a referral link for each repository.

    Methods:
        telegram_link: Adds a referral link to display in the list view.
        get_form: Customizes the model form to set the user field to the current user.
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

    def get_form(self, request, obj=None, **kwargs) -> BaseModelForm:
        """
        A custom method to set the user field to the current user.
        :param request: HttpRequest
        :param obj: Repository
        :param kwargs: dict
        :return: BaseModelForm
        """
        form = super().get_form(request, obj, **kwargs)

        form.base_fields["user"].initial = request.user
        form.base_fields["user"].disabled = True

        return form

    def get_queryset(self, request) -> QuerySet:
        """
        A custom method that returns the queryset filtered by the current user.
        :param request: HttpRequest
        :return: QuerySet
        """
        queryset = super().get_queryset(request)

        return queryset.filter(user=request.user)
