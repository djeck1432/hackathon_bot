from django.contrib import admin
from django.forms import BaseModelForm


class PredefinedUserAdminBase(admin.ModelAdmin):
    """
    A base class that contains common methods to avoid code repetitions

    Methods:
        get_form: Customizes the model form to set the user field to the current user.
    """

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
