from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models import QuerySet
from django.forms import BaseModelForm

from .models import Repository

admin.site.unregister(Group)


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
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
